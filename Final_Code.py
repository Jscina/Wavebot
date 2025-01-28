import cv2
import numpy as np
import picamera
import picamera.array
import time
import board
import busio
import adafruit_pca9685
import RPi.GPIO as GPIO
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
    pulse_length = (angle * 1000 // 180) + 1000  # angle to pulse length formula for SG90 servo
    duty_cycle = int(pulse_length * 65535 / (1 / pwm.frequency) / 1000000)
    pwm.channels[channel].duty_cycle = duty_cycle

def update_servos(x_val, y_val):
     # Calculate the angles for horizontal movement
    angle_diff = (x_val * (50) / 320)  # Calculate angle difference based on x_val
    if x_val < 0:  # If x_val is negative, the face is on the right side of the face
        lex_angle = 125 - angle_diff  # Adjusted calculation for left eye
        rex_angle = 130 - angle_diff  # Adjusted calculation for right eye
        # Set the servo angles for horizontal movement
        set_servo_angle(0, lex_angle)
        set_servo_angle(2, rex_angle)

    if x_val > 0:  # If x_val is negative, the face is on the left side of the face
        lex_angle = 125 + angle_diff  # Adjusted calculation for left eye
        rex_angle = 130 + angle_diff  # Adjusted calculation for right eye
        # Set the servo angles for horizontal movement
        set_servo_angle(0, lex_angle)
        set_servo_angle(2, rex_angle)

    # Calculate the angles for vertical movement
    ley_angle = 110 - (y_val * (120 - 300) / 240)  # Fixed the calculation for left eye
    rey_angle = 110 + (y_val * (110 - 300) / 240)

    # Set the servo angles for vertical movement
    set_servo_angle(1, ley_angle)
    set_servo_angle(3, rey_angle)

def center_servos():
    kit.servo[0].angle = 125
    kit.servo[1].angle = 120
    kit.servo[2].angle = 130
    kit.servo[3].angle = 110
    
    kit.servo[8].angle = 74
    kit.servo[9].angle = 20

model = cv2.dnn.readNetFromCaffe('deploy.prototxt', 'res10_300x300_ssd_iter_140000.caffemodel')

def detect_faces(frame):
    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, scalefactor=1.0, size=(300, 300), mean=(104, 177, 123), swapRB=True)
    
    # Pass the blob through the SSD model to detect faces
    model.setInput(blob)
    detections = model.forward()

    # Extract the bounding box coordinates and confidence scores for the faces
    faces = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            x1, y1, x2, y2 = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
            x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
            faces.append((x, y, w, h))

    return faces

def draw_faces(frame, faces, origin_x, origin_y):
    global last_face_detected
    
    if len(faces) == 0:
        return
        
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        center_x, center_y = x + w // 2, y + h // 2
        cv2.circle(frame, (center_x, center_y), 2, (0, 0, 255), -1)

        relative_x, relative_y = center_x - origin_x, origin_y - center_y
        reversed_x = origin_x - (center_x - origin_x)  # Reverse the x value
        text = f"({relative_x}, {relative_y})"
        cv2.putText(frame, text, (center_x + 5, center_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
        
        print(reversed_x, relative_y)
        update_servos(reversed_x, relative_y)  # Pass reversed_x instead of relative_x

        last_face_detected = time.time()

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

with picamera.PiCamera() as camera:
    camera.resolution = (width, height)
    camera.framerate = 30
    with picamera.array.PiRGBArray(camera, size=(width, height)) as stream:
        center_servos()
        last_face_detected = time.time()
        while True:
            # Capture frame
            camera.capture(stream, format='bgr', use_video_port=True)  # Get the frame data as a NumPy array
            frame = stream.array

            # Detect faces
            faces = detect_faces(frame)

            # Calculate the origin (center of the grid)
            origin_x, origin_y = width // 2, height // 2

            # Draw faces
            draw_faces(frame, faces, origin_x, origin_y)

            # Draw the quadrants
            draw_quadrants(frame)

            # Display the frame using OpenCV
            cv2.imshow('Live Footage', frame)

            # Clear the stream for the next frame
            stream.truncate(0)

            # Exit the loop when 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                        
            # Center the eyes if no face is detected for more than 5 seconds
            if time.time() - last_face_detected > 5:
                center_servos()
                last_face_detected = time.time()

cv2.destroyAllWindows()
