# Vision-Inertial Sign Language Translator

A Python-based edge computing system that translates hand gestures into text in real time. This project resolves the physical ambiguities of standard 2D camera feeds by fusing computer vision hand-tracking with 3D motion data from a wrist-mounted IMU.

## Technologies & Core Concepts

* **Edge Computing & Embedded Hardware:** Raspberry Pi 5 (Host), Arduino Nano 33 BLE Sense (Microcontroller), LSM9DS1 6-axis IMU
* **Computer Vision & Tracking:** OpenCV, Google MediaPipe (3D skeletal landmark extraction), NumPy
* **Concurrency & Systems Programming:** Python `threading` (Daemon workers, event flags), `collections.deque` (Thread-safe rolling window buffers)
* **Hardware I/O & Networking:** PySerial (115200 baud UART communication), UDP Sockets (Fire-and-forget telemetry streaming)
* **Algorithms & Signal Processing:** Distance-from-wrist rotation-invariant heuristics, Midpoint classification, Axis-dominant sensor fusion

## Core Modules

The codebase is modularized to separate hardware polling, computer vision inference, and state management. Sensor polling is completely decoupled from the main execution loop to prevent blocking the video pipeline.

* **`main.py` (Core Orchestrator):** The primary event loop. It synchronizes the vision and hardware subsystems, implements state-management logic (such as shape memory for dropped frames and temporal confirmation gates to prevent misfires), and renders a real-time OpenCV telemetry HUD.
* **`imu_reader.py` (Hardware I/O):** Runs a dedicated background daemon thread to continuously poll 6-axis serial data (accelerometer + gyroscope) from an Arduino at 50Hz. Data is pushed into a thread-safe sliding window, ensuring the main video thread is never blocked by serial I/O.
* **`vision.py` (Computer Vision):** Wraps Google MediaPipe to extract 21 3D hand landmarks. Uses custom distance-to-wrist geometric heuristics to classify static hand shapes (e.g., Palm, Index, Peace) in a way that is invariant to camera rotation.
* **`gesture_analyzer.py` (Fusion Engine):** Processes the 1-second rolling IMU buffer to classify physical motion vectors (e.g., Punch, Wag, Twist). It evaluates both the visual shape and the physical motion against a fusion table to output the final mapped word.
* **`audio_sender.py` (Networking):** A lightweight UDP socket client that transmits confirmed text translations over the local network to a remote host for audio synthesis.

## Testing Suite

The repository includes isolated testing scripts to verify subsystems without requiring the full hardware loop:
* `test_analyzer.py`: Unit tests for the gesture fusion logic using mocked IMU data arrays.
* `test_serial.py`: Diagnostic script to verify the Arduino serial connection and baud rate.
* `test_vision.py`: Isolated webcam testing for the MediaPipe shape classification.

## System Architecture

<img width="968" height="1545" alt="image" src="https://github.com/user-attachments/assets/896a4571-9d8e-4ffe-b0c0-82e83e90117c" />
