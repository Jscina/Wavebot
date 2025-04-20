# Wavebot Face Tracker

A Raspberry Pi-powered robot that uses a camera to detect faces and move servo motors (eyes, neck, etc.) to track them in real time. When a face is seen, Wavebot can also “wave” its arm!

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Enable I2C & Camera](#enable-i2c--camera)
  - [Install Dependencies](#install-dependencies)
- [Running the Program](#running-the-program)
- [How It Works](#how-it-works)
- [Code Overview](#code-overview)
- [Servo Channel Mapping](#servo-channel-mapping)
- [Configuration](#configuration)
- [Hardware Fallback](#hardware-fallback)

---

## Overview

Wavebot is a face-tracking robot that uses:

- **OpenCV** with a **Haar cascade** (rather than a heavier DNN) for face detection
- An **Adafruit PCA9685** PWM driver for multiple servo motors
- **ServoKit** (or fallback simulation) for controlling servo angles
- **concurrent.futures** for threading face detection without blocking servo updates
- A “**wave**” function to greet people when it detects a face

When a face enters view, Wavebot tracks it with its eyes and optionally waves. If a face disappears for 5 seconds, Wavebot re-centers its servos.

---

## Project Structure

```
wavebot/
│
├── main.py                    # Main entry point (threaded detection + wave logic)
├── README.md                  # Documentation (this file)
├── wavebot/
│   ├── __init__.py            # Package exports
│   ├── camera.py              # Camera setup (USB or PiCamera)
│   ├── config.py              # Constants and logger setup
│   ├── servos.py              # Servo motor logic (positions, wave, fallback)
│   └── vision.py              # Haar cascade face detection + tracking
└── model/
    └── haarcascade_frontalface_default.xml  # Haar cascade for face detection
```

- **`main.py`** orchestrates detection + servo control in a loop.
- **`vision.py`** has functions for detecting faces (with Haar cascades), selecting a “tracked face,” and drawing overlays.
- **`servos.py`** houses the servo logic (e.g., how angles map to PWM signals) plus the “wave” function.
- **`config.py`** defines constants like `FRAME_WIDTH`, `FRAME_HEIGHT`, servo channel mappings, and servo limits.
- **`camera.py`** yields frames from either a USB camera or a PiCamera.

---

## Setup Instructions

### Prerequisites

- **Raspberry Pi** (recommended) or another Linux system
- **PiCamera** or USB camera
- **Adafruit PCA9685** connected via I2C
- **Servo motors** for eyes, neck, and arm
- **Python 3.7+** (or higher)
- **Adequate power supply** (servos can draw significant current)

### Enable I2C & Camera

```bash
sudo raspi-config
# Navigate to "Interface Options" and enable I2C.
# Also enable the camera if you're using PiCamera.
```

### Install Dependencies

```bash
sudo apt update
sudo apt install python3-pip libatlas-base-dev
pip3 install --upgrade pip
pip3 install opencv-python adafruit-circuitpython-servokit
```

If you’re using a **PiCamera**, also install `picamera`:

```bash
sudo apt install python3-picamera
```

---

## Running the Program

1. **Clone or copy** this repository to your Raspberry Pi.
2. **Ensure** your camera is plugged in and I2C is wired to the PCA9685.
3. **Run the main script**:

```bash
python3 main.py
```

Wavebot will launch a real-time window. Press **q** to exit.

---

## How It Works

1. **Camera Feed**: `camera_stream()` yields frames from either PiCamera or a USB camera.
2. **Face Detection**: `detect_faces()` uses a Haar cascade to find faces.
3. **Tracking**: `pick_face_to_track()` chooses which face to “lock on” to if there are multiple.
4. **Servo Control**:
   - `update_servos(...)` adjusts the eyes/neck to follow the tracked face.
   - If a face is detected (and it’s been at least 5 seconds since the last wave), the `wave()` function is called to move the hand servo from 0° to 90° in a smooth loop.
5. **Timeout**: If no face is detected for 5 seconds, the servos automatically recenter.

---

## Code Overview

- **`main.py`**

  - Uses a `ThreadPoolExecutor` to do face detection without stalling servo updates.
  - Tracks timestamps for last face detection (`last_face_time`) and last wave (`last_wave_time`).
  - Waves if a face is seen and enough time has passed since the last wave.

- **`vision.py`**

  - Loads a Haar cascade classifier (`haarcascade_frontalface_default.xml`).
  - Has `detect_faces()`, `pick_face_to_track()`, and `draw_faces()` to handle face detection, tracking logic, and bounding box drawing.

- **`servos.py`**

  - Defines a fallback if hardware is unavailable.
  - `set_servo_angle()` clamps angles, logs movements, and sets PWM duty cycles.
  - `move_servo_gradually()` for smooth transitions between angles.
  - `update_servos()` uses a sigmoid-based factor for smoother tracking movements.
  - `wave()` moves the “hand” servo from 0° to 90° a few times to wave.
  - `center_servos()` resets all servos to neutral positions.

- **`camera.py`**

  - Provides a unified `camera_stream()` generator that yields frames from either a USB camera (`cv2.VideoCapture`) or PiCamera.
  - Controlled by `USE_USB_CAMERA` in `config.py`.

- **`config.py`**
  - Contains logging setup, frame size, camera selection, servo channel enumeration, and servo angle limits.

---

## Servo Channel Mapping

| Servo Channel | Purpose                     |
| ------------- | --------------------------- |
| 0             | Left Eye – Horizontal       |
| 1             | Left Eye – Vertical         |
| 2             | Right Eye – Horizontal      |
| 3             | Right Eye – Vertical        |
| 4             | Hand / Arm servo for waving |
| 8             | Neck – Horizontal           |
| 9             | Neck – Vertical             |

All channels and their angle limits are specified in `config.py`.

---

## Configuration

You can modify these settings in `wavebot/config.py`:

- **`FRAME_WIDTH`** and **`FRAME_HEIGHT`**: camera resolution
- **`USE_USB_CAMERA`**: `False` by default to use PiCamera, set to `True` for a USB camera
- **`SERVO_LIMITS`**: angle limits for each servo channel
- **`logging` level**: set to `DEBUG` for more detailed logs, or `INFO` for standard logs

---

## Hardware Fallback

If the code detects that the PCA9685 or Adafruit ServoKit isn’t installed or isn’t available, it logs a warning and switches to a **simulation mode**:

- Servo angles are recorded in an in-memory dictionary.
- No real PWM signals are sent.
- You can still observe logs of servo movements for testing.

Similarly, if PiCamera is unavailable (e.g., you’re on a PC or a Pi without the camera module attached), the code automatically attempts to use a USB camera.

---

That’s it! Once you have everything set up, **Wavebot** will watch for faces, track them with its eyes, and wave every few seconds it sees someone. Enjoy tinkering, and feel free to customize further!
