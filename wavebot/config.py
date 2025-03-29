from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
