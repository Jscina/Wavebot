import argparse
import logging
import cv2
import time
from wavebot import (
    ServoController,
    camera_stream,
    detect_faces,
    draw_faces,
    draw_quadrants,
    logger,
)
from wavebot.vision import FaceBoxList


parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true", help="Enable logging")
args, _ = parser.parse_known_args()
ENABLE_LOGGING = args.debug

if ENABLE_LOGGING:
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.WARNING)


def main() -> None:
    """
    Main loop for face detection and servo control.
    """
    servo_controller = ServoController()
    servo_controller.start()
    servo_controller.queue_center_servos()
    last_face_time = time.time()

    frame_count = 0
    faces: FaceBoxList = []

    for frame in camera_stream():
        frame_count += 1

        if frame_count % 3 == 0:
            faces = detect_faces(frame)

        def on_face_detected() -> None:
            nonlocal last_face_time
            last_face_time = time.time()

        face_detected = draw_faces(servo_controller, frame, faces, on_face_detected)
        draw_quadrants(frame)

        cv2.imshow("Live Footage", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        # If no face for 5s, recenter servos
        if not face_detected and (time.time() - last_face_time > 5):
            logger.info("No face detected for 5s, recentering servos")
            servo_controller.queue_center_servos()
            last_face_time = time.time()

    servo_controller.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
