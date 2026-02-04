Iris Liveness Verification Project
==================================
This project provides an on-the-spot iris + liveliness verification system using a laptop/webcam for image capture
and an ESP32-CAM (used as hardware controller) for indicating success/failure via LEDs, buzzer, or relay.

Folder structure:
- main.py            # launcher
- gui.py             # Tkinter GUI
- liveliness.py      # iris detection & liveliness logic (uses cvzone.FaceMeshDetector)
- utils/constants.py # thresholds and landmark indices
- utils/iris_functions.py # helper functions: EAR, circularity, etc.
- hardware/esp32_controller.ino # ESP32 Arduino sketch (HTTP server)

Requirements:
- Python 3.8+
- OpenCV (`pip install opencv-python`)
- cvzone (`pip install cvzone`)
- mediapipe (installed by cvzone)
- Pillow (`pip install pillow`)
- requests (`pip install requests`)

Usage:
1. Install requirements
2. Modify ESP32 IP in `liveliness.py` (ESP32 should be running the provided sketch)
3. Run: `python main.py`
4. Click the "Start Liveliness Test" button to begin verification.

Notes:
- The project intentionally uses the laptop/webcam for high-quality capture.
- ESP32-CAM is used only as a hardware controller (LEDs/relay) and NOT for image capture.
