import socket
import time

# --- Configuration ---
# These must match exactly what receiver.py uses on the laptop
LAPTOP_IP   = "192.168.137.1"   # Windows laptop IP over ICS ethernet
LAPTOP_PORT = 65432
TIMEOUT     = 2.0               # seconds

_sock = None

def _get_sock():
    """Lazy-initializes the UDP socket."""
    global _sock
    if _sock is None:
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.settimeout(TIMEOUT)
    return _sock

def send_word(word):
    """
    Sends a recognized word string to the laptop over UDP.
    UDP is fire-and-forget — no connection needed, never blocks.

    Args:
        word: str — e.g. "HELLO", "STOP", "YOU"
    """
    try:
        sock = _get_sock()
        message = word.encode("utf-8")
        sock.sendto(message, (LAPTOP_IP, LAPTOP_PORT))
        print(f"[AUDIO] Sent: {word}")
    except Exception as e:
        print(f"[AUDIO] Send failed: {e}")

def close():
    global _sock
    if _sock is not None:
        _sock.close()
        _sock = None