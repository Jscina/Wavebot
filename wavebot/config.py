from enum import IntEnum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EyesChannel(IntEnum):
    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 2
    RIGHT_Y = 3


class ExtraChannel(IntEnum):
    EXTRA_1 = 8
    EXTRA_2 = 9


FRAME_WIDTH = 320
FRAME_HEIGHT = 240

USE_USB_CAMERA = False
