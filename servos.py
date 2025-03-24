import logging
from config import EYE_CHANNELS, EXTRA_CHANNELS

log = logging.getLogger(__name__)

HARDWARE_AVAILABLE: bool = False

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


def set_servo_angle(channel: int, angle: float) -> None:
    """
    Sets the servo at 'channel' to 'angle' degrees.

    If running on a platform without hardware,
    it only logs the call instead of actually moving a servo.
    """
    log.info("set_servo_angle(channel=%d, angle=%.2f)", channel, angle)

    if not HARDWARE_AVAILABLE:
        return

    pulse_length: float = (angle * 1000 // 180) + 1000
    duty_cycle: int = int(pulse_length * 65535 / (1 / pwm.frequency) / 1_000_000)
    pwm.channels[channel].duty_cycle = duty_cycle


def update_servos(x_val: int, y_val: int, width: int, height: int) -> None:
    """
    Moves the eye servos based on face coordinates.

    :param x_val: Horizontal offset of face center from the frame's center.
                  (Negative => left, Positive => right)
    :param y_val: Vertical offset of face center from the frame's center.
                  (Negative => below center, Positive => above center)
    :param width: Frame width in pixels.
    :param height: Frame height in pixels.

    If hardware isn't available, this only logs calls.
    """
    log.info(
        "update_servos(x_val=%d, y_val=%d, width=%d, height=%d)",
        x_val,
        y_val,
        width,
        height,
    )

    if not HARDWARE_AVAILABLE:
        return

    angle_diff: float = x_val * 50.0 / width

    if x_val < 0:
        set_servo_angle(EYE_CHANNELS["left_x"], 125 - angle_diff)
        set_servo_angle(EYE_CHANNELS["right_x"], 130 - angle_diff)
    elif x_val > 0:
        set_servo_angle(EYE_CHANNELS["left_x"], 125 + angle_diff)
        set_servo_angle(EYE_CHANNELS["right_x"], 130 + angle_diff)

    ley_angle: float = 110 - (y_val * (120 - 300) / height)
    rey_angle: float = 110 + (y_val * (110 - 300) / height)

    set_servo_angle(EYE_CHANNELS["left_y"], ley_angle)
    set_servo_angle(EYE_CHANNELS["right_y"], rey_angle)


def center_servos() -> None:
    """
    Resets all servo motors to their default center positions.

    If hardware isn't available, this only logs calls.
    """
    log.info("center_servos() called")

    if not HARDWARE_AVAILABLE:
        return

    # Real servo logic from your original code:
    kit.servo[EYE_CHANNELS["left_x"]].angle = 125
    kit.servo[EYE_CHANNELS["left_y"]].angle = 120
    kit.servo[EYE_CHANNELS["right_x"]].angle = 130
    kit.servo[EYE_CHANNELS["right_y"]].angle = 110
    kit.servo[EXTRA_CHANNELS["extra_1"]].angle = 74
    kit.servo[EXTRA_CHANNELS["extra_2"]].angle = 20
