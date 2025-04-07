import cv2
import time
import concurrent.futures
from wavebot import (
    camera_stream,
    center_servos,
    detect_faces,
    pick_face_to_track,
    draw_faces,
    draw_quadrants,
    logger,
    wave,
)

last_face_time = time.time()
last_wave_time = 0
WAVE_INTERVAL = 5


def on_face_detected() -> None:
    global last_face_time
    last_face_time = time.time()


def main() -> None:
    global last_face_time, last_wave_time
    center_servos()
    last_face_time = time.time()
    last_wave_time = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for frame in camera_stream():
            future = executor.submit(detect_faces, frame)
            faces = future.result()

            tracked = pick_face_to_track(faces)
            face_found = draw_faces(frame, tracked, on_face_detected)
            draw_quadrants(frame)

            if face_found:
                current_time = time.time()
                if current_time - last_wave_time > WAVE_INTERVAL:
                    wave()
                    last_wave_time = current_time

            cv2.imshow("Live Footage", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            if not face_found and (time.time() - last_face_time > 5):
                logger.info("No face detected for 5 seconds. Centering servos.")
                center_servos()
                last_face_time = time.time()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
