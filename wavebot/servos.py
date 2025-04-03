import time
from queue import Queue
from threading import Thread

from .config import Channel, SERVO_LIMITS, logger

HARDWARE_AVAILABLE: bool = False

DEFAULT_SERVO_POSITIONS: dict[int, float] = {
    Channel.EYE_LEFT_X.value: 140.0,
    Channel.EYE_LEFT_Y.value: 90.0,
    Channel.EYE_RIGHT_X.value: 155.0,
    Channel.EYE_RIGHT_Y.value: 115.0,
    Channel.NECK_X.value: 70.0,
    Channel.NECK_Y.value: 75.0,
}

SERVO_POSITIONS: dict[int, float] = dict(DEFAULT_SERVO_POSITIONS)

try:
    import adafruit_pca9685
    import board
    import busio
    from adafruit_servokit import ServoKit

    i2c = busio.I2C(board.SCL, board.SDA)
    pwm = adafruit_pca9685.PCA9685(i2c)
    pwm.frequency = 60
    kit = ServoKit(channels=16)
    HARDWARE_AVAILABLE = True
    logger.warning("Successfully initialized PCA9685 servo hardware.")
except (ImportError, OSError, AttributeError) as exc:
    logger.warning(f"Hardware not available: {exc}")
    logger.warning("Falling back to dummy servo functions (no real servo movement).")


def set_servo_angle(channel: Channel, angle: float) -> None:
    """
    Immediately sets the servo at 'channel' to 'angle' degrees on this thread,
    clamped to a safe range. Updates SERVO_POSITIONS.
    This is called inside the worker thread (or if hardware is not available).
    """
    old_angle = SERVO_POSITIONS.get(channel.value, 0.0)
    servo_min, servo_max = SERVO_LIMITS.get(channel.value, (0.0, 180.0))
    clamped_angle = max(servo_min, min(angle, servo_max))
    servo_type = channel.__class__.__name__

    logger.info(
        f"set_servo_angle({servo_type}.{channel.name}): "
        f"old={old_angle:.2f} → requested={angle:.2f} → clamped={clamped_angle:.2f} "
        f"(HW={HARDWARE_AVAILABLE})"
    )

    SERVO_POSITIONS[channel.value] = clamped_angle

    if not HARDWARE_AVAILABLE:
        return

    pulse_length: float = (clamped_angle * 1000 // 180) + 1000
    duty_cycle: int = int(pulse_length * 65535 / (1 / pwm.frequency) / 1_000_000)
    pwm.channels[channel.value].duty_cycle = duty_cycle


class ServoController:
    """
    Manages all servo commands via a background worker thread.
    Commands are queued; the worker processes them sequentially.
    Supports:
      - Gradual movement
      - Re-centering
      - Face-tracking updates
    """

    def __init__(self):
        self._command_queue = Queue()
        self._thread = Thread(target=self._worker, daemon=True)
        self._running = False

    def start(self):
        """Starts the worker thread if it's not already running."""
        if not self._running:
            self._running = True
            self._thread.start()
            logger.info("Servo worker thread started.")

    def stop(self):
        """Stops the worker thread gracefully."""
        self._command_queue.put(None)
        self._thread.join()
        logger.info("Servo worker thread stopped.")

    def queue_servo_angle(self, channel: Channel, angle: float):
        """
        Immediately queue a single servo angle command.
        The worker will call 'set_servo_angle' internally.
        """
        self._command_queue.put(("MOVE", channel, angle))

    def queue_move_servo_gradually(
        self,
        channel: Channel,
        target_angle: float,
        step: float = 1.0,
        delay: float = 0.1,
    ):
        """
        Moves the given servo channel from its current angle to 'target_angle',
        step-by-step, inserting a small delay between each sub-step.
        This entire motion is queued and processed asynchronously.
        """
        current_angle = SERVO_POSITIONS.get(channel.value, 90.0)
        servo_min, servo_max = SERVO_LIMITS.get(channel.value, (0.0, 180.0))
        target_clamped = max(servo_min, min(target_angle, servo_max))

        if current_angle < target_clamped:
            angle_range = range(int(current_angle), int(target_clamped) + 1, int(step))
        else:
            angle_range = range(int(current_angle), int(target_clamped) - 1, -int(step))

        for ang in angle_range:
            clamped_ang = max(servo_min, min(float(ang), servo_max))
            self._command_queue.put(("MOVE", channel, clamped_ang))
            if delay > 0:
                self._command_queue.put(("SLEEP", delay))

        self._command_queue.put(("MOVE", channel, target_clamped))

    def queue_center_servos(self):
        """
        Resets all servo motors to their original (default) positions
        as stored in DEFAULT_SERVO_POSITIONS.
        Each command is queued so they move in sequence, but not gradually.
        """
        logger.info(f"queue_center_servos() called (HW={HARDWARE_AVAILABLE})")
        for channel_val, default_angle in DEFAULT_SERVO_POSITIONS.items():
            channel = Channel(channel_val)
            self._command_queue.put(("MOVE", channel, default_angle))

    def queue_update_servos(self, x_val: int, y_val: int, width: int, height: int):
        """
        Moves the eye and neck servos based on face coordinates (async).
        """
        logger.info(
            f"update_servos(x_val={x_val}, y_val={y_val}, width={width}, height={height})"
        )

        eye_x_angle_diff: float = x_val * 50.0 / width
        neck_x_angle_diff: float = x_val * 25.0 / width

        if x_val < 0:
            self.queue_servo_angle(Channel.EYE_LEFT_X, 125.0 - eye_x_angle_diff)
            self.queue_servo_angle(Channel.EYE_RIGHT_X, 130.0 - eye_x_angle_diff)
        elif x_val > 0:
            self.queue_servo_angle(Channel.EYE_LEFT_X, 125.0 + eye_x_angle_diff)
            self.queue_servo_angle(Channel.EYE_RIGHT_X, 130.0 + eye_x_angle_diff)

        ley_angle: float = 110.0 - (y_val * (120.0 - 300.0) / height)
        rey_angle: float = 110.0 + (y_val * (110.0 - 300.0) / height)
        self.queue_servo_angle(Channel.EYE_LEFT_Y, ley_angle)
        self.queue_servo_angle(Channel.EYE_RIGHT_Y, rey_angle)

        current_neck_x = SERVO_POSITIONS[Channel.NECK_X.value]
        new_neck_x = current_neck_x
        if abs(x_val) > width // 6:
            if x_val < 0:
                new_neck_x = 74.0 - neck_x_angle_diff
            else:
                new_neck_x = 74.0 + neck_x_angle_diff
        if new_neck_x != current_neck_x:
            self.queue_move_servo_gradually(Channel.NECK_X, new_neck_x)

        neck_y_angle_diff: float = y_val * 20.0 / height
        current_neck_y = SERVO_POSITIONS[Channel.NECK_Y.value]
        new_neck_y = current_neck_y
        if abs(y_val) > height // 6:
            if y_val > 0:
                new_neck_y = 20.0 - neck_y_angle_diff
            else:
                new_neck_y = 20.0 + neck_y_angle_diff
        if new_neck_y != current_neck_y:
            self.queue_move_servo_gradually(Channel.NECK_Y, new_neck_y)

    def _worker(self):
        """
        Worker thread loop:
          - Fetch commands from the queue
          - 'MOVE' => call set_servo_angle
          - 'SLEEP' => time.sleep
          - None => exit
        """
        while True:
            command = self._command_queue.get()
            if command is None:
                break

            cmd_type = command[0]
            if cmd_type == "MOVE":
                _, channel, angle = command
                set_servo_angle(channel, angle)

            elif cmd_type == "SLEEP":
                _, duration = command
                time.sleep(duration)

            self._command_queue.task_done()
