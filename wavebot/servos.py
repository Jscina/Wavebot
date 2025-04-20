import time
import math
from .config import Channel, SERVO_LIMITS, logger, EYE_LEFT_X_CENTER, EYE_RIGHT_X_CENTER, NECK_X_CENTER, HAND_RIGHT_CENTER

HARDWARE_AVAILABLE = False

servo_positions = {
    Channel.EYE_LEFT_X.value: EYE_LEFT_X_CENTER,
    Channel.EYE_RIGHT_X.value: EYE_RIGHT_X_CENTER,
    Channel.NECK_X.value: NECK_X_CENTER,
    Channel.HAND_RIGHT.value: HAND_RIGHT_CENTER,
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
    Sets the servo at the given channel to the specified angle.
    Angle is clamped based on SERVO_LIMITS and logged.
    """
    old_angle = servo_positions.get(channel.value, 0.0)
    servo_min, servo_max = SERVO_LIMITS.get(channel.value, (0.0, 180.0))
    clamped_angle = max(servo_min, min(angle, servo_max))
    logger.info(
        f"set_servo_angle({channel.name}): old={old_angle:.2f} → requested={angle:.2f} → clamped={clamped_angle:.2f} (HW={HARDWARE_AVAILABLE})"
    )
    servo_positions[channel.value] = clamped_angle

    if HARDWARE_AVAILABLE:
        pulse_length = (clamped_angle * 1000 // 180) + 1000
        duty_cycle = int(pulse_length * 65535 / (1 / pwm.frequency) / 1_000_000)
        pwm.channels[channel.value].duty_cycle = duty_cycle


def move_servo_gradually(
    channel: Channel, target_angle: float, step: float = 1.0, delay: float = 0.05
) -> None:
    """
    Smoothly moves a servo from its current position to the target angle.
    """
    current_angle = servo_positions.get(channel.value, 90.0)
    servo_min, servo_max = SERVO_LIMITS.get(channel.value, (0.0, 180.0))
    target_angle = max(servo_min, min(target_angle, servo_max))

    if current_angle < target_angle:
        angle_range = range(int(current_angle), int(target_angle) + 1, int(step))
    else:
        angle_range = range(int(current_angle), int(target_angle) - 1, -int(step))

    for ang in angle_range:
        set_servo_angle(channel, float(ang))
        time.sleep(delay)
    set_servo_angle(channel, target_angle)


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def update_servos(x_val: int, y_val: int, width: int, height: int) -> None:
    """
    Updates servo angles based on the x and y offsets from the frame center.
    Uses a non-linear (sigmoid) mapping for smooth adjustments.
    """
    linear_factor = (x_val * 50.0) / width
    smooth_factor = linear_factor * sigmoid(linear_factor / 10.0)

    left_eye_x = EYE_LEFT_X_CENTER + smooth_factor
    right_eye_x = EYE_RIGHT_X_CENTER + smooth_factor

    logger.info(
        f"update_servos: x_val={x_val}, y_val={y_val}, smooth_factor={smooth_factor:.2f}"
    )
    set_servo_angle(Channel.EYE_LEFT_X, left_eye_x)
    set_servo_angle(Channel.EYE_RIGHT_X, right_eye_x)

    movement_percent = min(1.0, max(-1.0, x_val / (width / 2)))

    if movement_percent < 0:
        new_neck_x = NECK_X_CENTER + (movement_percent * (NECK_X_CENTER - SERVO_LIMITS[Channel.NECK_X.value][0]))
    else:
        new_neck_x = NECK_X_CENTER + (movement_percent * (SERVO_LIMITS[Channel.NECK_X.value][1] - NECK_X_CENTER))

    if abs(x_val) > (width // 6):
        logger.info(
            f"NECK MOVEMENT: x_val={x_val}, percent={movement_percent:.2f}, new_angle={new_neck_x:.2f}"
        )
        if (
            abs(new_neck_x - servo_positions.get(Channel.NECK_X.value, NECK_X_CENTER))
            > 1.0
        ):
            move_servo_gradually(Channel.NECK_X, new_neck_x)


def wave() -> None:
    """
    Waves at the person using smooth servo movement from 0° to 90°.
    """
    logger.info("Waving")
    if not HARDWARE_AVAILABLE:
        return
    for _ in range(2):
        move_servo_gradually(Channel.HAND_RIGHT, 0, step=5, delay=0.05)
        move_servo_gradually(Channel.HAND_RIGHT, 90, step=5, delay=0.05)


def center_servos() -> None:
    """
    Centers all servos to their default positions.
    """
    logger.info("Centering servos")
    set_servo_angle(Channel.EYE_LEFT_X, EYE_LEFT_X_CENTER)
    set_servo_angle(Channel.EYE_RIGHT_X, EYE_RIGHT_X_CENTER)
    set_servo_angle(Channel.NECK_X, NECK_X_CENTER)
    set_servo_angle(Channel.HAND_RIGHT, HAND_RIGHT_CENTER)
