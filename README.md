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
├── calibrate.py                  # Main application entry point
├── pyproject.toml           # Project dependencies and metadata
├── wavebot/
│   ├── __init__.py          # Package exports
│   ├── camera.py            # Camera setup (PiCamera or USB camera)
│   ├── config.py            # Constants (servo channels, frame size, camera settings)
│   ├── servos.py            # Servo motor control logic
│   └── vision.py            # Face detection & rendering logic
├── model/                   # Face detection model files
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
# Install dependencies
uv sync

# Run the program
uv run main.py
```

## 📚 Documentation

The project is documented using pdoc3, which creates HTML documentation from docstrings in the code.

### Generating Documentation

```bash
# Generate HTML documentation
uv run pdoc --html wavebot -o docs/
```

### Viewing Documentation

After generating the documentation, you can view it by opening the HTML files in your browser:

```bash
# If you have python installed
python -m http.server -d docs

# Or simply open the file directly
xdg-open docs/wavebot/index.html  # Linux
open docs/wavebot/index.html      # macOS
start docs/wavebot/index.html     # Windows
```

### Documentation

The generated documentation includes:

- **API Reference**: Detailed documentation of all modules, classes, and functions
- **Module Overview**: High-level description of each module's purpose
- **Function Signatures**: Parameters, return types, and descriptions

You can find documentation for the main components:

- `camera.py`: Camera stream interface implementation
- `config.py`: Configuration constants and logger setup
- `servos.py`: Servo motor control and angle calculations
- `vision.py`: Face detection and visualization functions

---

## 🎯 How It Works

- The camera captures a live video feed (either from PiCamera or USB camera).
- The DNN face detection model finds faces in the frame.
- Based on the face's position, eye servos (X/Y for each eye) move to track it.
- The eyes reset to center if no face is detected for 5 seconds.
- The system will automatically detect if hardware is available and fall back to a simulation mode if not.

---

## 🧠 Servo Channel Mapping

| Servo Channel | Description            |
| ------------- | ---------------------- |
| 0             | Left Eye – Horizontal  |
| 1             | Left Eye – Vertical    |
| 2             | Right Eye – Horizontal |
| 3             | Right Eye – Vertical   |
| 8             | Neck - Horizontal      |
| 9             | Neck - Vertical        |

All channels are defined as Enums in `config.py`.

---

## ⚙️ Configuration

You can adjust the following settings in `wavebot/config.py`:

- `FRAME_WIDTH` and `FRAME_HEIGHT`: Camera resolution
- `USE_USB_CAMERA`: Set to `True` to use a USB webcam instead of PiCamera

---

## 🛠 Code Overview

### `main.py`

- Runs the capture + processing loop
- Calls functions from the wavebot package
- Keeps track of time since last face detection
- Recenters servos if no face is detected for 5 seconds

### `wavebot/servos.py`

- Converts angles to PWM signals
- Functions to center or update servo positions
- Includes graceful fallback if hardware is unavailable
- Maintains in-memory state of servo positions

### `wavebot/vision.py`

- Loads the OpenCV face detector
- Draws bounding boxes + grid overlay
- Calculates servo movement based on face location
- Shows coordinates of detected faces

### `wavebot/camera.py`

- Provides a unified camera stream interface
- Supports both PiCamera and USB cameras via OpenCV
- Configurable via settings in `config.py`

### `wavebot/config.py`

- Central place for frame size and channel assignments
- Enum classes for servo channels
- Camera selection settings

---

## 📸 Model Info

The face detection model is a **Caffe-based SSD (Single Shot Detector)** trained on ResNet10.

Files are in the `wavebot/model` folder:

- `deploy.prototxt`
- `res10_300x300_ssd_iter_140000.caffemodel`

This model runs **in real-time on a Pi** and is good enough for face tracking (not recognition).

---

## 🤖 Hardware Fallback

The system is designed to handle hardware limitations:

- If the PCA9685 hardware is unavailable, the system switches to simulation mode.
- If the PiCamera is unavailable, it defaults to using a USB camera.
- All hardware interactions are logged for debugging purposes.
