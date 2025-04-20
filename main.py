import cv2
import time
import threading
import concurrent.futures
from picamera import PiCamera
from picamera.array import PiRGBArray
from wavebot import (
    center_servos,
    detect_faces,
    pick_face_to_track,
    draw_faces,
    draw_quadrants,
    logger,
    wave,
)
from wavebot.config import FRAME_WIDTH, FRAME_HEIGHT


def wave_in_thread():
    """Run the wave function in a separate thread"""
    thread = threading.Thread(target=wave)
    thread.daemon = True
    thread.start()
    return thread


def main() -> None:
    center_servos()
    last_face_time = time.time()
    last_wave_time = 0
    WAVE_INTERVAL = 5
    wave_thread = None

    with PiCamera() as camera:
        camera.resolution = (FRAME_WIDTH, FRAME_HEIGHT)
        camera.framerate = 30
        with PiRGBArray(camera, size=(FRAME_WIDTH, FRAME_HEIGHT)) as stream:
            center_servos()

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                for frame_data in camera.capture_continuous(
                    stream, format="bgr", use_video_port=True
                ):
                    frame = frame_data.array

                    future = executor.submit(detect_faces, frame.copy())
                    faces = future.result()

                    tracked = pick_face_to_track(faces)
                    face_found = draw_faces(frame, tracked, lambda: None)
                    draw_quadrants(frame)

                    current_time = time.time()
                    if face_found:
                        last_face_time = current_time
                        if current_time - last_wave_time > WAVE_INTERVAL and (
                            wave_thread is None or not wave_thread.is_alive()
                        ):
                            wave_thread = wave_in_thread()
                            last_wave_time = current_time

                    cv2.imshow("Live Footage", frame)
                    stream.truncate(0)

                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                    if not face_found and (current_time - last_face_time > 5):
                        logger.info("No face detected for 5 seconds. Centering servos.")
                        center_servos()
                        last_face_time = current_time

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
