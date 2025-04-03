from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Wavebot")

FRAME_WIDTH = 320
FRAME_HEIGHT = 240

USE_USB_CAMERA = False


class Channel(Enum):
    """Mapping of servo motor channels to their corresponding GPIO pins"""

    EYE_LEFT_X = 0
    EYE_LEFT_Y = 1
    EYE_RIGHT_X = 2
    EYE_RIGHT_Y = 3
    NECK_X = 8
    NECK_Y = 9


SERVO_LIMITS = {
    Channel.EYE_LEFT_X.value: (130.0, 160.0),
    Channel.EYE_LEFT_Y.value: (55.0, 135.0),
    Channel.EYE_RIGHT_X.value: (100.0, 180.0),
    Channel.EYE_RIGHT_Y.value: (60.0, 140.0),
    Channel.NECK_X.value: (20.0, 110.0),
    Channel.NECK_Y.value: (60.0, 80.0),
}
