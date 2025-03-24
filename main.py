import cv2
import time
from wavebot import (
    camera_stream,
    detect_faces,
    draw_faces,
    draw_quadrants,
    center_servos,
    logger,
)


def main() -> None:
    """
    Main loop for face detection and servo control.
    """
    center_servos()
    last_face_time = time.time()

    for frame in camera_stream():
        faces = detect_faces(frame)

        # Callback function to update last face detection time
        def on_face_detected() -> None:
            nonlocal last_face_time
            last_face_time = time.time()

        face_detected = draw_faces(frame, faces, on_face_detected)
        draw_quadrants(frame)

        cv2.imshow("Live Footage", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        # If no face for 5s, recenter servos
        if not face_detected and (time.time() - last_face_time > 5):
            logger.info("No face detected for 5s, recentering servos")
            center_servos()
            last_face_time = time.time()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
