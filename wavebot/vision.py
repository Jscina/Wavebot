import cv2
import numpy as np
from typing import Callable, Optional
from .config import FRAME_WIDTH, FRAME_HEIGHT
from .servos import update_servos

FaceBox = tuple[int, int, int, int]

tracked_face: Optional[FaceBox] = None

face_cascade = cv2.CascadeClassifier("model/haarcascade_frontalface_default.xml")


def detect_faces(frame: np.ndarray) -> list[FaceBox]:
    """
    Detects faces using a Haar cascade, replicating the behavior from Final_Code.py.
    Returns the output of detectMultiScale (typically a numpy array of bounding boxes).
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6)
    if faces is None or len(faces) == 0:
        return []
    return list(faces)  # type: ignore


def pick_face_to_track(faces: list[FaceBox]) -> Optional[FaceBox]:
    """
    Selects and updates a single face to track.
    If a face was already being tracked, it prefers a face close to the previous one.
    Otherwise, it chooses the largest face.
    """
    global tracked_face

    if not faces:
        tracked_face = None
        return None

    if tracked_face is None:
        tracked_face = max(faces, key=lambda box: box[2] * box[3])
        return tracked_face

    x_t, y_t, w_t, h_t = tracked_face
    center_t = (x_t + w_t / 2, y_t + h_t / 2)

    best_match = tracked_face
    best_distance = float("inf")
    for x, y, w, h in faces:
        center_current = (x + w / 2, y + h / 2)
        distance = (
            (center_current[0] - center_t[0]) ** 2
            + (center_current[1] - center_t[1]) ** 2
        ) ** 0.5
        if distance < best_distance or (w * h > w_t * h_t):
            best_distance = distance
            best_match = (x, y, w, h)
    tracked_face = best_match
    return tracked_face


def draw_faces(
    frame: np.ndarray, face_box: Optional[FaceBox], on_face_detected: Callable[[], None]
) -> bool:
    """
    Draws the tracked face on the frame and updates servo positions using a smooth mapping.
    Returns True if a face is drawn.
    """
    if face_box is None:
        return False

    x, y, w, h = face_box
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
    center_x = x + w // 2
    center_y = y + h // 2
    cv2.circle(frame, (center_x, center_y), 2, (0, 0, 255), -1)

    origin_x = FRAME_WIDTH // 2
    origin_y = FRAME_HEIGHT // 2
    offset_x = center_x - origin_x
    offset_y = origin_y - center_y

    update_servos(-offset_x, offset_y, FRAME_WIDTH, FRAME_HEIGHT)
    on_face_detected()

    cv2.putText(
        frame,
        f"({offset_x}, {offset_y})",
        (center_x + 5, center_y - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (0, 0, 0),
        1,
    )
    return True


def draw_quadrants(frame: np.ndarray) -> None:
    """
    Draws horizontal and vertical center lines on the frame.
    """
    rows, cols = frame.shape[:2]
    cv2.line(frame, (0, rows // 2), (cols, rows // 2), (0, 255, 0), 1)
    cv2.line(frame, (cols // 2, 0), (cols // 2, rows), (0, 255, 0), 1)
