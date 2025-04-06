import time
from .config import Channel, SERVO_LIMITS, logger

HARDWARE_AVAILABLE: bool = False

servo_positions: dict[int, float] = {
    Channel.EYE_LEFT_X.value: 140.0,
    Channel.EYE_LEFT_Y.value: 70.0,
    Channel.EYE_RIGHT_X.value: 155.0,
    Channel.EYE_RIGHT_Y.value: 110.0,
    Channel.NECK_X.value: 70.0,
    Channel.NECK_Y.value: 75.0,
}


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
    logger.info("Successfully initialized PCA9685 servo hardware.")
except (ImportError, OSError, AttributeError) as exc:
    logger.warning(f"Hardware not available: {exc}")
    logger.warning("Falling back to dummy servo functions (no real servo movement).")


def set_servo_angle(channel: Channel, angle: float) -> None:
    """
    Sets the servo at 'channel' to 'angle' degrees, clamped to a safe range.
    Logs which servo is being moved, old → new angles, and whether hardware is used.
    Updates an in-memory dictionary to allow simulation or replay if hardware is absent.
    """
    old_angle = servo_positions.get(channel.value, 0.0)
    servo_min, servo_max = SERVO_LIMITS.get(channel.value, (0.0, 180.0))
    clamped_angle = max(servo_min, min(angle, servo_max))
    servo_type = channel.__class__.__name__

    logger.info(
        f"set_servo_angle({servo_type}.{channel.name}): "
        f"old={old_angle:.2f} → requested={angle:.2f} → clamped={clamped_angle:.2f} "
        f"(HW={HARDWARE_AVAILABLE})"
    )

    servo_positions[channel.value] = clamped_angle

    if not HARDWARE_AVAILABLE:
        return

    pulse_length: float = (clamped_angle * 1000 // 180) + 1000
    duty_cycle: int = int(pulse_length * 65535 / (1 / pwm.frequency) / 1_000_000)
    pwm.channels[channel.value].duty_cycle = duty_cycle


def move_servo_gradually(
    channel: Channel,
    target_angle: float,
    step: float = 1.0,
    delay: float = 0.1,
) -> None:
    """
    Moves servo from its current angle to 'target_angle' smoothly in increments.
    Each increment waits 'delay' seconds, clamping at each step.
    """
    current_angle = servo_positions.get(channel.value, 90.0)
    servo_min, servo_max = SERVO_LIMITS.get(channel.value, (0.0, 180.0))
    target_clamped = max(servo_min, min(target_angle, servo_max))

    if current_angle < target_clamped:
        angle_range = range(int(current_angle), int(target_clamped) + 1, int(step))
    else:
        angle_range = range(int(current_angle), int(target_clamped) - 1, -int(step))

    for ang in angle_range:
        clamped_ang = max(servo_min, min(float(ang), servo_max))
        set_servo_angle(channel, clamped_ang)
        time.sleep(delay)

    set_servo_angle(channel, target_clamped)


def wave() -> None:
    """
    Waves the right hand servo by moving it to 0 degrees and back to 90 degrees.
    """
    if HARDWARE_AVAILABLE:
        for _ in range(2):
            set_servo_angle(Channel.HAND_RIGHT, 0.0)
            set_servo_angle(Channel.HAND_RIGHT, 90.0)
    else:
        logger.info("Waving (simulated, no hardware available)")


def update_servos(x_val: int, y_val: int, width: int, height: int) -> None:
    """
    Moves the eye and neck servos based on face coordinates.
    Angles are clamped internally by set_servo_angle().
    """
    logger.info(
        f"update_servos(x_val={x_val}, y_val={y_val}, width={width}, height={height})"
    )

    eye_x_angle_diff: float = x_val * 50.0 / width
    neck_x_angle_diff: float = x_val * 25.0 / width

    if x_val < 0:
        set_servo_angle(Channel.EYE_LEFT_X, 125.0 - eye_x_angle_diff)
        set_servo_angle(Channel.EYE_RIGHT_X, 130.0 - eye_x_angle_diff)
    elif x_val > 0:
        set_servo_angle(Channel.EYE_LEFT_X, 125.0 + eye_x_angle_diff)
        set_servo_angle(Channel.EYE_RIGHT_X, 130.0 + eye_x_angle_diff)

    ley_angle: float = 110.0 - (y_val * (120.0 - 300.0) / height)
    rey_angle: float = 110.0 + (y_val * (110.0 - 300.0) / height)

    set_servo_angle(Channel.EYE_LEFT_Y, ley_angle)
    set_servo_angle(Channel.EYE_RIGHT_Y, rey_angle)

    wave()

    current_neck_x = servo_positions[Channel.NECK_X.value]
    new_neck_x = current_neck_x
    if abs(x_val) > width // 6:
        if x_val < 0:
            new_neck_x = 74.0 - neck_x_angle_diff
        else:
            new_neck_x = 74.0 + neck_x_angle_diff
    if new_neck_x != current_neck_x:
        move_servo_gradually(Channel.NECK_X, new_neck_x)

    neck_y_angle_diff: float = y_val * 20.0 / height
    current_neck_y = servo_positions[Channel.NECK_Y.value]
    new_neck_y = current_neck_y
    if abs(y_val) > height // 6:
        if y_val > 0:
            new_neck_y = 20.0 - neck_y_angle_diff
        else:
            new_neck_y = 20.0 + neck_y_angle_diff
    if new_neck_y != current_neck_y:
        move_servo_gradually(Channel.NECK_Y, new_neck_y)


def center_servos() -> None:
    """
    Resets all servo motors to their default center positions.
    Logs the action, then calls set_servo_angle on each channel.
    """
    logger.info(f"center_servos() called (HW={HARDWARE_AVAILABLE})")
    set_servo_angle(Channel.EYE_LEFT_X, 140.0)
    set_servo_angle(Channel.EYE_LEFT_Y, 90.0)
    set_servo_angle(Channel.EYE_RIGHT_X, 155.0)
    set_servo_angle(Channel.EYE_RIGHT_Y, 115.0)
    set_servo_angle(Channel.NECK_X, 70.0)
    set_servo_angle(Channel.NECK_Y, 75.0)
    set_servo_angle(Channel.HAND_RIGHT, 45.0)
