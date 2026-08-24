"""
imu_reader.py
Thread 1: Serial listener for Arduino IMU data.

Runs as a daemon thread. Continuously reads CSV lines
from the Arduino over USB Serial and pushes 7-element
tuples into a shared deque.

Tuple format: (timestamp, ax, ay, az, gx, gy, gz)
Deque size  : 50 samples = exactly 1.0 second at 50Hz
"""

import serial
import threading
import time
from collections import deque

# --- Shared State ---
# This deque is the ONLY object shared between Thread 1 and Thread 2.
# deque is thread-safe for append/read operations in Python.
imu_buffer = deque(maxlen=50)

# Flag to signal the thread to stop cleanly
_stop_event = threading.Event()

# --- Configuration ---
PORT      = "/dev/ttyACM0"
BAUD_RATE = 115200


def _reader_loop():
    """
    Internal loop. Runs inside the daemon thread.
    Opens Serial port and continuously pushes samples into imu_buffer.
    """
    print("[IMU] Starting Serial reader thread...")

    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)              # Wait for Arduino to reset after port open
        ser.reset_input_buffer()   # Discard stale startup bytes
        print(f"[IMU] Connected on {PORT} at {BAUD_RATE} baud.")

        while not _stop_event.is_set():
            raw = ser.readline()
            if not raw:
                continue  # Timeout, just loop again

            try:
                parts = raw.decode("utf-8").strip().split(",")
                if len(parts) != 6:
                    continue  # Malformed line, skip

                ax, ay, az = float(parts[0]), float(parts[1]), float(parts[2])
                gx, gy, gz = float(parts[3]), float(parts[4]), float(parts[5])

                # Timestamp uses Pi's clock, not Arduino's
                # This prevents drift and gives us consistent time windows
                ts = time.monotonic()

                imu_buffer.append((ts, ax, ay, az, gx, gy, gz))

            except (ValueError, UnicodeDecodeError):
                # Bad byte or non-numeric value — silently skip
                continue

        ser.close()
        print("[IMU] Serial port closed.")

    except serial.SerialException as e:
        print(f"[IMU] FATAL: Could not open {PORT}: {e}")
        print("[IMU] Check: Is Arduino plugged in? Is another program using the port?")


def start():
    """
    Starts the IMU reader as a background daemon thread.
    Call this once at program startup.
    """
    t = threading.Thread(target=_reader_loop, name="IMU-Reader", daemon=True)
    t.start()
    return t


def stop():
    """Signals the reader thread to exit cleanly."""
    _stop_event.set()


def get_snapshot():
    """
    Returns a stable snapshot (list) of the current deque contents.
    Thread 2 calls this to get the last 1 second of IMU data.
    Converting to list prevents issues if deque updates mid-analysis.
    """
    return list(imu_buffer)
