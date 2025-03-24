# 👋 Wavebot Face Tracker

A Raspberry Pi-powered robot that uses a camera to detect faces and move its eyes accordingly using servo motors.

This project uses:

- OpenCV with a pre-trained DNN face detection model
- Adafruit PCA9685 PWM controller
- ServoKit for servo control
- Camera support for both PiCamera and USB cameras
- Modular Python code with clean separation between vision, servos, and logic

---

## 📁 Project Structure

```text
wavebot/
│
├── main.py                  # Main application entry point
├── config.py                # Constants (servo channels, frame size, camera settings)
├── servos.py                # Servo motor control logic
├── vision.py                # Face detection & rendering logic
├── camera.py                # Camera setup (PiCamera or USB camera)
├── model/
│   ├── deploy.prototxt      # Face detection model config
│   └── res10_300x300...     # Pre-trained Caffe model
└── README.md                # You're reading it :)
```

---

## ⚙️ Setup Instructions

### 📌 Prerequisites

Run this on a **Raspberry Pi** with:

- PiCamera module connected and enabled OR a USB camera
- PCA9685 servo driver wired via I2C
- 4+ servos wired to the PCA9685 board
- Python 3.11+
- Proper power supply for servos (IMPORTANT)

### 🔧 Enable I2C & PiCamera

```bash
sudo raspi-config
# Enable both I2C and Camera under Interfaces
```

### 📦 Install Dependencies

```bash
sudo apt update
sudo apt install python3-pip libatlas-base-dev
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.11
```

## 🚀 Running the Program

```bash
uv sync
uv run main.py
```

---

## 🎯 How It Works

- The camera captures a live video feed (either from PiCamera or USB camera).
- The DNN face detection model finds faces in the frame.
- Based on the face's position, eye servos (X/Y for each eye) move to track it.
- If no face is detected for 5 seconds, the eyes reset to center.
- The system will automatically detect if hardware is available and fall back to a simulation mode if not.

---

## 🧠 Servo Channel Mapping

| Servo Channel | Description                |
| ------------- | -------------------------- |
| 0             | Left Eye – Horizontal      |
| 1             | Left Eye – Vertical        |
| 2             | Right Eye – Horizontal     |
| 3             | Right Eye – Vertical       |
| 8             | Extra servo (configurable) |
| 9             | Extra servo (configurable) |

All channels are defined as Enums in `config.py`.

---

## ⚙️ Configuration

You can adjust the following settings in `config.py`:

- `FRAME_WIDTH` and `FRAME_HEIGHT`: Camera resolution
- `USE_USB_CAMERA`: Set to `True` to use a USB webcam instead of PiCamera

---

## 🛠 Code Overview

### `main.py`

- Runs the capture + processing loop
- Calls functions from other modules
- Keeps track of time since last face detection
- Recenters servos if no face is detected for 5 seconds

### `servos.py`

- Converts angles to PWM signals
- Functions to center or update servo positions
- Includes graceful fallback if hardware is unavailable
- Maintains in-memory state of servo positions

### `vision.py`

- Loads the OpenCV face detector
- Draws bounding boxes + grid overlay
- Calculates servo movement based on face location
- Shows coordinates of detected faces

### `camera.py`

- Provides a unified camera stream interface
- Supports both PiCamera and USB cameras via OpenCV
- Configurable via settings in `config.py`

### `config.py`

- Central place for frame size and channel assignments
- Enum classes for servo channels
- Camera selection settings

---

## 📸 Model Info

The face detection model used is a **Caffe-based SSD (Single Shot Detector)** trained on ResNet10.

Files are in the `/model` folder:

- `deploy.prototxt`
- `res10_300x300_ssd_iter_140000.caffemodel`

This model runs **in real-time on a Pi** and is good enough for face tracking (not recognition).

---

## 🤖 Hardware Fallback

The system is designed to handle hardware limitations:

- If the PCA9685 hardware is unavailable, the system switches to simulation mode.
- If the PiCamera is unavailable, it defaults to using a USB camera.
- All hardware interactions are logged for debugging purposes.
