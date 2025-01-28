import cv2
import numpy as np
import busio
import board
import adafruit_pca9685
import threading

# Load the face detection model
model_weights = "res10_300x300_ssd_iter_140000.caffemodel"
model_config = "deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(model_config, model_weights)

# Initialize the servo hat
i2c = busio.I2C(board.SCL, board.SDA)
hat = adafruit_pca9685.PCA9685(i2c)
hat.frequency = 50

# Define the servo channels
pan_channel = 0
tilt_channel = 1

# Initialize the camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Define the origin box
center_x, center_y = int(640/2), int(480/2)
box_size = 100
box_x1 = center_x - box_size//2
box_y1 = center_y - box_size//2
box_x2 = center_x + box_size//2
box_y2 = center_y + box_size//2

# Define a shared variable for the x coordinate
x_lock = threading.Lock()
shared_x = 0

# Define a function to control the pan servo
def pan_servo(angle):
    pulse = int(np.interp(angle, [-90, 90], [1100, 1900]))
    with x_lock:
        hat.channels[pan_channel].duty_cycle = int(pulse * 65535 / 1000000)

# Define a function to control the tilt servo
def tilt_servo(angle):
    pulse = int(np.interp(angle, [-90, 90], [1100, 1900]))
    hat.channels[tilt_channel].duty_cycle = int(pulse * 65535 / 1000000)

# Define a function for the face tracking thread
def face_track():
    global shared_x
    while True:
        # Read a frame from the camera
        ret, frame = cap.read()

        # Detect faces in the frame using the SSD model
        blob = cv2.dnn.blobFromImage(frame, 1.0, (640, 480), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        # Loop over the face detections
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            # If the confidence is high enough, track the face
            if confidence > 0.8:
                box = detections[0, 0, i, 3:7] * np.array([640, 480, 640, 480])
                (startX, startY, endX, endY) = box.astype("int")
                face_centerpoint_x = int((startX + endX) / 2)
                face_centerpoint_y = int((startY + endY) / 2)

                # Calculate the x and y coordinates relative to the origin (center of the grid)
                x = face_centerpoint_x - center_x
                y = center_y - face_centerpoint_y
                
                # Check if the center point is inside the box around the origin
                if box_x1 <= face_centerpoint_x <= box_x2 and box_y1 <= face_centerpoint_y <= box_y2:
                    text = f"x = {x}, y = {y} (inside box)"
                else:
                    text = f"x = {x}, y = {y}"

                # Move the servo based on the x-coordinate
                if x < -10:
                    angle = 0
                elif x > 10:
                    angle = 180
                else:
                    angle = 90
                move_servo(angle)

        # Display the frame (optional)
        cv2.imshow("Output", frame)

        # Exit the program if "q" is pressed
        if cv2.waitKey(1) == ord("q"):
            break

#Clean up
cap.release()
cv2.destroyAllWindows()
