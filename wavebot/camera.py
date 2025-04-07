import cv2
import sys
from .config import FRAME_WIDTH, FRAME_HEIGHT, USE_USB_CAMERA, logger

try:
    from picamera import PiCamera  # type: ignore
    from picamera.array import PiRGBArray  # type: ignore
except ImportError:
    PiCamera = None
    PiRGBArray = None


class Camera:
    def __init__(self):
        self.use_usb = USE_USB_CAMERA or PiCamera is None
        self.cap = None
        self.camera = None
        self.stream = None
        self.iterator = None

        if self.use_usb:
            logger.info("Using USB camera")
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            if not self.cap.isOpened():
                print("Could not open USB camera.", file=sys.stderr)
        else:
            logger.info("Using PiCamera")
            self.camera = PiCamera()  # type: ignore
            self.camera.resolution = (FRAME_WIDTH, FRAME_HEIGHT)
            self.camera.framerate = 30
            self.stream = PiRGBArray(self.camera, size=(FRAME_WIDTH, FRAME_HEIGHT))  # type: ignore
            self.iterator = self.camera.capture_continuous(
                self.stream, format="bgr", use_video_port=True
            )

    def read(self):
        if self.use_usb:
            if self.cap is None:
                return None
            ret, frame = self.cap.read()
            return frame if ret else None
        else:
            try:
                frame_data = next(self.iterator)
                frame = frame_data.array
                self.stream.truncate(0)
                self.stream.seek(0)
                return frame
            except StopIteration:
                return None

    def release(self):
        if self.use_usb and self.cap:
            self.cap.release()
        elif self.camera:
            if self.stream:
                self.stream.close()
            self.camera.close()
