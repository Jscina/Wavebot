import cv2
import numpy as np
import picamera
import picamera.array
import time
import board
import busio
import math
import adafruit_pca9685
import RPi.GPIO as GPIO
import concurrent.futures
from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

# Set up the PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pwm = adafruit_pca9685.PCA9685(i2c)
pwm.frequency = 60

# Define width and height
width, height = 320, 240


def draw_quadrants(frame):
    rows, cols, _ = frame.shape
    center_row, center_col = rows // 2, cols // 2
    cv2.line(frame, (0, center_row), (cols, center_row), (0, 255, 0), 1)
    cv2.line(frame, (center_col, 0), (center_col, rows), (0, 255, 0), 1)


def set_servo_angle(channel, angle):
    pulse_length = (
        angle * 1000 // 180
    ) + 1000  # angle to pulse length formula for SG90 servo
    duty_cycle = int(pulse_length * 65535 / (1 / pwm.frequency) / 1000000)
    pwm.channels[channel].duty_cycle = duty_cycle


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def calculate_eye_angles(x_val, y_val):
    # Calculate the angles for horizontal movement
    angle_diff = x_val * (50) / 320  # Calculate angle difference based on x_val

    if x_val < 0:  # If x_val is negative, the face is on the right side of the face
        lex_angle = (
            125 - angle_diff * sigmoid(angle_diff) - 3
        )  # Adjusted calculation for left eye
        rex_angle = (
            130 - angle_diff * sigmoid(angle_diff) - 3
        )  # Adjusted calculation for right eye

    if x_val > 0:  # If x_val is negative, the face is on the left side of the face
        lex_angle = (
            125 + angle_diff * sigmoid(angle_diff) - 3
        )  # Adjusted calculation for left eye
        rex_angle = (
            130 + angle_diff * sigmoid(angle_diff) - 3
        )  # Adjusted calculation for right eye

    # Calculate the angles for vertical movement
    vertical_angle_diff = 15  # Adjust this value to match the difference between the eyes' initial vertical positions
    vertical_sensitivity_factor = 0.4
    ley_angle = (
        120 - (y_val * vertical_sensitivity_factor / 1.5 * (120 - 300) / 240)
    ) + vertical_angle_diff
    rey_angle = (
        (110 + (y_val * vertical_sensitivity_factor / 1.5 * (110 - 300) / 240))
        + vertical_angle_diff
        + 3
    )

    return lex_angle, ley_angle, rex_angle, rey_angle


def update_servos(x_val, y_val):
    lex_angle, ley_angle, rex_angle, rey_angle = calculate_eye_angles(x_val, y_val)

    # Set the servo angles
    set_servo_angle(0, lex_angle)
    set_servo_angle(1, ley_angle)
    set_servo_angle(2, rex_angle)
    set_servo_angle(3, rey_angle)


def update_neck_x_servo(x_val):
    neck_x_center = 74
    neck_x_range = 25
    k_p_x = neck_x_range / (width // 2)  # Proportional gain for x-axis
    error_x = (width // 2) - x_val  # Invert the sign of the error
    neck_x_angle = neck_x_center - k_p_x * error_x
    neck_x_angle = max(
        30, min(100, neck_x_angle)
    )  # Limit the neck x angle between 50 and 100
    set_servo_angle(8, neck_x_angle)


def update_neck_y_servo(y_val):
    print("")
    """
    neck_y_center = 100
    neck_y_range = 30
    k_p_y = neck_y_range / (height // 2)  # Proportional gain for y-axis
    error_y = (height // 2) - y_val
    neck_y_angle = neck_y_center + k_p_y * error_y
    neck_y_angle = max(110, min(80, neck_y_angle))  # Limit the neck y angle between 0 and 60
    set_servo_angle(9, neck_y_angle)
"""


def center_servos():
    kit.servo[0].angle = 125
    kit.servo[1].angle = 120
    kit.servo[2].angle = 130
    kit.servo[3].angle = 110

    kit.servo[8].angle = 74  # Neck X
    kit.servo[9].angle = 100  # Neck Y


face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")


def detect_faces(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=7)
    return faces


# Add this global variable after the last_face_detected variable
tracked_face = None


def draw_faces(frame, faces, origin_x, origin_y):
    global last_face_detected
    global tracked_face

    if len(faces) == 0:
        tracked_face = None
        return

    # Find the face that should be tracked
    if tracked_face is None:
        closest_face = None
        max_area = 0

        # Find the face with the largest area
        for x, y, w, h in faces:
            area = w * h
            if area > max_area:
                max_area = area
                closest_face = (x, y, w, h)

        tracked_face = closest_face

    # Check if the tracked face is still in the frame and update its position if a closer face is found
    x, y, w, h = tracked_face
    tracked_face_area = w * h
    for x, y, w, h in faces:
        area = w * h
        if area > tracked_face_area:
            tracked_face = (x, y, w, h)
            tracked_face_area = area
        elif abs(tracked_face[0] - x) <= w and abs(tracked_face[1] - y) <= h:
            tracked_face = (x, y, w, h)

    # Draw the tracked face and update servos
    x, y, w, h = tracked_face
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
    center_x, center_y = x + w // 2, y + h // 2
    cv2.circle(frame, (center_x, center_y), 2, (0, 0, 255), -1)

    relative_x, relative_y = center_x - origin_x, origin_y - center_y
    reversed_x = origin_x - (center_x - origin_x)  # Reverse the x value
    text = f"({relative_x}, {relative_y})"
    cv2.putText(
        frame,
        text,
        (center_x + 5, center_y - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )

    # print(reversed_x, relative_y)
    update_servos(reversed_x, relative_y)  # Pass reversed_x instead of relative_x

    last_face_detected = time.time()

    # Update neck servos
    update_neck_x_servo(reversed_x)
    update_neck_y_servo(relative_y)


face_cascade = cv2.CascadeClassifier("model/haarcascade_frontalface_default.xml")

with picamera.PiCamera() as camera:
    center_servos()
    camera.resolution = (width, height)
    camera.framerate = 30
    with picamera.array.PiRGBArray(camera, size=(width, height)) as stream:
        center_servos()
        last_face_detected = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            while True:
                # Capture frame
                camera.capture(
                    stream, format="bgr", use_video_port=True
                )  # Get the frame data as a NumPy array
                frame = stream.array

                # Detect faces
                origin_x, origin_y = width // 2, height // 2

                future = executor.submit(detect_faces, frame)
                faces = future.result()

                # Draw faces and update servos
                draw_faces(frame, faces, origin_x, origin_y)

                # Draw the quadrants
                draw_quadrants(frame)

                # Display the frame using OpenCV
                cv2.imshow("Live Footage", frame)

                # Clear the stream for the next frame
                stream.truncate(0)

                # Exit the loop when 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                # Center the eyes if no face is detected for more than 5 seconds
                if time.time() - last_face_detected > 5:
                    center_servos()
                    last_face_detected = time.time()

cv2.destroyAllWindows()
