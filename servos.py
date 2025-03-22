import board
import busio
import adafruit_pca9685
from adafruit_servokit import ServoKit
from config import EYE_CHANNELS, EXTRA_CHANNELS

kit = ServoKit(channels=16)
i2c = busio.I2C(board.SCL, board.SDA)
pwm = adafruit_pca9685.PCA9685(i2c)
pwm.frequency = 60


def set_servo_angle(channel: int, angle: float) -> None:
    """
    Converts a given angle into a PWM duty cycle and applies it to the specified channel.
    """
    pulse_length = (angle * 1000 // 180) + 1000
    duty_cycle = int(pulse_length * 65535 / (1 / pwm.frequency) / 1_000_000)
    pwm.channels[channel].duty_cycle = duty_cycle


def update_servos(x_val: int, y_val: int, width: int, height: int) -> None:
    """
    Moves the eye servos based on face coordinates.
    :param x_val: Horizontal offset of face center.
    :param y_val: Vertical offset of face center.
    :param width: Frame width.
    :param height: Frame height.
    """
    angle_diff: float = x_val * 50 / width

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
    """
    kit.servo[EYE_CHANNELS["left_x"]].angle = 125
    kit.servo[EYE_CHANNELS["left_y"]].angle = 120
    kit.servo[EYE_CHANNELS["right_x"]].angle = 130
    kit.servo[EYE_CHANNELS["right_y"]].angle = 110
    kit.servo[EXTRA_CHANNELS["extra_1"]].angle = 74
    kit.servo[EXTRA_CHANNELS["extra_2"]].angle = 20
