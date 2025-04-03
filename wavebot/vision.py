import cv2
import numpy as np
from typing import Callable
from .servos import ServoController
from .config import FRAME_WIDTH, FRAME_HEIGHT
from pathlib import Path

base_model_path = Path(__file__).parent.parent / "model"
caffe_model_path = base_model_path / "deploy.prototxt"
caffe_weights_path = base_model_path / "res10_300x300_ssd_iter_140000.caffemodel"

model = cv2.dnn.readNetFromCaffe(
    caffe_model_path.as_posix(), caffe_weights_path.as_posix()
)

FaceBoxList = list[tuple[int, int, int, int]]


def detect_faces(frame: np.ndarray) -> FaceBoxList:
    """
    Detects faces in a frame using OpenCV's DNN model.
    :param frame: Input image frame.
    :return: List of bounding boxes (x, y, w, h).
    """
    height, width = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104, 177, 123), swapRB=True)
    model.setInput(blob)
    detections = model.forward()

    faces: FaceBoxList = []
    for i in range(detections.shape[2]):
        confidence: float = detections[0, 0, i, 2]
        if confidence > 0.5:
            x1, y1, x2, y2 = detections[0, 0, i, 3:7] * np.array(
                [width, height, width, height]
            )
            faces.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1)))
    return faces


def draw_faces(
    controller: ServoController,
    frame: np.ndarray,
    faces: FaceBoxList,
    on_face_detected: Callable[[], None],
) -> bool:
    """
    Draws bounding boxes and centers the eyes on detected faces.
    :param frame: Image to draw on.
    :param faces: List of face bounding boxes.
    :param on_face_detected: Callback when a face is found.
    :return: True if face detected, False otherwise.
    """
    if not faces:
        return False

    origin_x = FRAME_WIDTH // 2
    origin_y = FRAME_HEIGHT // 2

    for x, y, w, h in faces:
        center_x = x + w // 2
        center_y = y + h // 2
        relative_x = center_x - origin_x
        relative_y = origin_y - center_y
        reversed_x = origin_x - (center_x - origin_x)

        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.circle(frame, (center_x, center_y), 2, (0, 0, 255), -1)
        cv2.putText(
            frame,
            f"({relative_x}, {relative_y})",
            (center_x + 5, center_y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 0, 0),
            1,
        )

        controller.queue_update_servos(
            reversed_x, relative_y, FRAME_WIDTH, FRAME_HEIGHT
        )
        on_face_detected()

    return True


def draw_quadrants(frame: np.ndarray) -> None:
    """
    Draws vertical and horizontal center lines.
    """
    rows, cols = frame.shape[:2]
    cv2.line(frame, (0, rows // 2), (cols, rows // 2), (0, 255, 0), 1)
    cv2.line(frame, (cols // 2, 0), (cols // 2, rows), (0, 255, 0), 1)
