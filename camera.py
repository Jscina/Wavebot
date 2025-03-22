from config import FRAME_WIDTH, FRAME_HEIGHT
from picamera import PiCamera
from picamera.array import PiRGBArray


def camera_stream() -> tuple[PiCamera, PiRGBArray]:
    """
    Initializes and returns the PiCamera and its RGB array stream.
    """
    camera = PiCamera()
    camera.resolution = (FRAME_WIDTH, FRAME_HEIGHT)
    camera.framerate = 30
    stream = PiRGBArray(camera, size=(FRAME_WIDTH, FRAME_HEIGHT))
    return camera, stream
