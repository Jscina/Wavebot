import logging
from typing import Dict
from config import EyeChannel, ExtraChannel

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

HARDWARE_AVAILABLE: bool = False

servo_positions: Dict[int, float] = {
    EyeChannel.LEFT_X.value: 125.0,
    EyeChannel.LEFT_Y.value: 120.0,
    EyeChannel.RIGHT_X.value: 130.0,
    EyeChannel.RIGHT_Y.value: 110.0,
    ExtraChannel.EXTRA_1.value: 74.0,
    ExtraChannel.EXTRA_2.value: 20.0,
}

try:
    import board
    import busio
    import adafruit_pca9685
    from adafruit_servokit import ServoKit

    i2c = busio.I2C(board.SCL, board.SDA)
    pwm = adafruit_pca9685.PCA9685(i2c)
    pwm.frequency = 60

    kit = ServoKit(channels=16)
    HARDWARE_AVAILABLE = True
    log.info("Successfully initialized PCA9685 servo hardware.")

except (ImportError, OSError, AttributeError) as exc:
    log.warning("Hardware not available: %s", exc)
    log.warning("Falling back to dummy servo functions (no real servo movement).")


def set_servo_angle(channel: EyeChannel | ExtraChannel, angle: float) -> None:
    """
    Sets the servo (eye or extra) at 'channel' to 'angle' degrees.

    Logs which servo is being moved, old → new angles, and whether hardware is used.
    Updates an in-memory dictionary to allow simulation or replay if hardware is absent.
    """
    old_angle = servo_positions.get(channel.value, 0.0)

    servo_type = channel.__class__.__name__

    log.info(
        "set_servo_angle(%s.%s): old=%.2f → new=%.2f (HW=%s)",
        servo_type,
        channel.name,
        old_angle,
        angle,
        HARDWARE_AVAILABLE,
    )

    servo_positions[channel.value] = angle

    if not HARDWARE_AVAILABLE:
        return

    pulse_length: float = (angle * 1000 // 180) + 1000
    duty_cycle: int = int(pulse_length * 65535 / (1 / pwm.frequency) / 1_000_000)
    pwm.channels[channel.value].duty_cycle = duty_cycle


def update_servos(x_val: int, y_val: int, width: int, height: int) -> None:
    """
    Moves the eye servos based on face coordinates.

    Logs the (x_val, y_val) offset and updates the servo angles accordingly.
    """
    log.info(
        "update_servos(x_val=%d, y_val=%d, width=%d, height=%d)",
        x_val,
        y_val,
        width,
        height,
    )

    angle_diff: float = x_val * 50.0 / width

    if x_val < 0:
        set_servo_angle(EyeChannel.LEFT_X, 125.0 - angle_diff)
        set_servo_angle(EyeChannel.RIGHT_X, 130.0 - angle_diff)
    elif x_val > 0:
        set_servo_angle(EyeChannel.LEFT_X, 125.0 + angle_diff)
        set_servo_angle(EyeChannel.RIGHT_X, 130.0 + angle_diff)

    ley_angle: float = 110.0 - (y_val * (120.0 - 300.0) / height)
    rey_angle: float = 110.0 + (y_val * (110.0 - 300.0) / height)

    set_servo_angle(EyeChannel.LEFT_Y, ley_angle)
    set_servo_angle(EyeChannel.RIGHT_Y, rey_angle)


def center_servos() -> None:
    """
    Resets all servo motors to their default center positions.

    Logs the action, then calls set_servo_angle on each channel.
    """
    log.info("center_servos() called (HW=%s)", HARDWARE_AVAILABLE)

    set_servo_angle(EyeChannel.LEFT_X, 125.0)
    set_servo_angle(EyeChannel.LEFT_Y, 120.0)
    set_servo_angle(EyeChannel.RIGHT_X, 130.0)
    set_servo_angle(EyeChannel.RIGHT_Y, 110.0)

    set_servo_angle(ExtraChannel.EXTRA_1, 74.0)
    set_servo_angle(ExtraChannel.EXTRA_2, 20.0)
