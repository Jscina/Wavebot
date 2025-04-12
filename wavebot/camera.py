from typing import Generator
import cv2
import numpy as np
import sys

from .config import FRAME_WIDTH, FRAME_HEIGHT, USE_USB_CAMERA, logger

try:
    from picamera import PiCamera  # type: ignore
    from picamera.array import PiRGBArray  # type: ignore
except ImportError:
    PiCamera = None
    PiRGBArray = None


def camera_stream() -> Generator[np.ndarray, None, None]:
    """
    Yields frames (as np.ndarray) from either PiCamera (if USE_USB_CAMERA=False)
    or from USB camera via OpenCV VideoCapture (if USE_USB_CAMERA=True).
    """
    if USE_USB_CAMERA or PiCamera is None:
        logger.info("Using USB camera")
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            print("Could not open USB camera.", file=sys.stderr)
            return

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                yield frame
        finally:
            cap.release()

    else:
        logger.info("Using PiCamera")
        camera = PiCamera()
        try:
            camera.resolution = (FRAME_WIDTH, FRAME_HEIGHT)
            camera.framerate = 30
            stream = PiRGBArray(camera, size=(FRAME_WIDTH, FRAME_HEIGHT))  # type: ignore
            try:
                for frame_data in camera.capture_continuous(
                    stream, format="bgr", use_video_port=True
                ):
                    frame = frame_data.array
                    yield frame
                    # Clear the PiRGBArray to prepare for next frame
                    stream.truncate(0)
                    stream.seek(0)
            finally:
                stream.close()
        finally:
            camera.close()
