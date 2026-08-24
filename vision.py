import cv2
import mediapipe as mp
import math

mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles  = mp.solutions.drawing_styles

hands_detector = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6
)

WRIST=0
THUMB_TIP=4
INDEX_TIP=8;  INDEX_MCP=5;  INDEX_PIP=6
MIDDLE_TIP=12; MIDDLE_MCP=9; MIDDLE_PIP=10
RING_TIP=16;  RING_MCP=13;  RING_PIP=14
PINKY_TIP=20; PINKY_MCP=17; PINKY_PIP=18

_cap = None

def _get_cap():
    global _cap
    if _cap is None or not _cap.isOpened():
        _cap = cv2.VideoCapture(0)
        _cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        _cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        _cap.set(cv2.CAP_PROP_FPS, 30)
    return _cap

def _dist(a, b):
    """Euclidean distance between two landmarks in normalized coords."""
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

def _is_extended(lm, tip, mcp, pip):
    """
    Finger is extended if:
    1. Tip is farther from wrist than MCP (knuckle) — orientation independent
    2. Tip is farther from wrist than PIP — confirms full extension
    This works regardless of hand rotation angle.
    """
    tip_dist = _dist(lm[tip],  lm[WRIST])
    mcp_dist = _dist(lm[mcp],  lm[WRIST])
    pip_dist = _dist(lm[pip],  lm[WRIST])
    return tip_dist > mcp_dist and tip_dist > pip_dist

def _classify_shape(lm):
    index_up  = _is_extended(lm, INDEX_TIP,  INDEX_MCP,  INDEX_PIP)
    middle_up = _is_extended(lm, MIDDLE_TIP, MIDDLE_MCP, MIDDLE_PIP)
    ring_up   = _is_extended(lm, RING_TIP,   RING_MCP,   RING_PIP)
    pinky_up  = _is_extended(lm, PINKY_TIP,  PINKY_MCP,  PINKY_PIP)

    thumb_diff = lm[WRIST].y - lm[THUMB_TIP].y
    thumb_up   = thumb_diff > 0.15

    fingers_up = sum([index_up, middle_up, ring_up, pinky_up])

    # PALM: all four fingers extended, thumb not in thumbs-up
    if fingers_up == 4 and not thumb_up:
        return "PALM"

    # PEACE: index + middle only
    if index_up and middle_up and not ring_up and not pinky_up:
        return "PEACE"

    # INDEX: only index
    if index_up and not middle_up and not ring_up and not pinky_up:
        return "INDEX"

    # THUMB: thumb high, index not extended
    if thumb_up and not index_up:
        return "THUMB"

    return "UNKNOWN"

def get_frame_and_shape():
    cap = _get_cap()
    ret, frame = cap.read()
    if not ret or frame is None:
        import numpy as np
        return np.zeros((480,640,3), dtype="uint8"), "NONE"
    frame = cv2.flip(frame, 1)
    rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands_detector.process(rgb)
    shape  = "NONE"
    if result.multi_hand_landmarks:
        hl = result.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(
            frame, hl,
            mp_hands.HAND_CONNECTIONS,
            mp_styles.get_default_hand_landmarks_style(),
            mp_styles.get_default_hand_connections_style()
        )
        shape = _classify_shape(hl.landmark)
    return frame, shape

def release():
    global _cap
    if _cap is not None:
        _cap.release()
        _cap = None