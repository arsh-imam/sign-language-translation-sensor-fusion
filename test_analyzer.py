import time
from gesture_analyzer import analyze, get_word

def make_snapshot(ax_vals, ay_vals, az_vals,
                  gx_vals, gy_vals, gz_vals):
    """
    Creates a snapshot from explicit value lists.
    Each list must have exactly 50 elements.
    """
    ts = time.monotonic()
    return [
        (ts + i*0.02,
         ax_vals[i], ay_vals[i], az_vals[i],
         gx_vals[i], gy_vals[i], gz_vals[i])
        for i in range(50)
    ]

def flat(v, n=50):
    """50 identical values — simulates no movement on that axis."""
    return [v] * n

def spike(base, peak, n=50):
    """
    Simulates a motion spike: starts at base, ramps to peak
    at the midpoint, returns to base. Realistic gesture shape.
    """
    result = []
    for i in range(n):
        if i < 10:
            result.append(base)
        elif i < 25:
            result.append(base + (peak - base) * ((i - 10) / 15))
        elif i < 40:
            result.append(peak - (peak - base) * ((i - 25) / 15))
        else:
            result.append(base)
    return result

print("=== Gesture Analyzer Unit Tests ===\n")

# STILL: everything flat near resting values
still_snap = make_snapshot(
    ax_vals=flat(-0.32), ay_vals=flat(0.05), az_vals=flat(0.92),
    gx_vals=flat(4.0),   gy_vals=flat(1.0),  gz_vals=flat(1.0)
)

# PUNCH: ax spikes from -0.32 to +0.80 (range = 1.12g)
# ay stays flat, gyro low
punch_snap = make_snapshot(
    ax_vals=spike(-0.32, 0.80),
    ay_vals=flat(0.05),
    az_vals=flat(0.60),
    gx_vals=flat(10.0),
    gy_vals=flat(5.0),
    gz_vals=flat(5.0)
)

# WAG: ay spikes from -0.60 to +0.60 (range = 1.20g)
# ax stays flat
wag_snap = make_snapshot(
    ax_vals=flat(-0.10),
    ay_vals=spike(-0.60, 0.60),
    az_vals=flat(0.60),
    gx_vals=flat(5.0),
    gy_vals=flat(5.0),
    gz_vals=flat(5.0)
)

# TWIST: gy spikes to 110 deg/s
twist_snap = make_snapshot(
    ax_vals=flat(-0.20),
    ay_vals=flat(0.10),
    az_vals=flat(0.80),
    gx_vals=flat(20.0),
    gy_vals=spike(0.0, 110.0),
    gz_vals=flat(10.0)
)

tests = [
    ("STILL hand",    still_snap,  "STILL"),
    ("PUNCH forward", punch_snap,  "PUNCH"),
    ("WAG sideways",  wag_snap,    "WAG"),
    ("TWIST wrist",   twist_snap,  "TWIST"),
]

all_passed = True
for name, snapshot, expected in tests:
    result = analyze(snapshot)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_passed = False
    print(f"  [{status}] {name}: expected={expected}, got={result}")

print()
print("=== Fusion Table Tests ===\n")

fusion_tests = [
    ("INDEX", "PUNCH", "YOU"),
    ("INDEX", "WAG",   "NO"),
    ("INDEX", "STILL", "ONE"),
    ("PALM",  "TWIST", "MINE"),
    ("PALM",  "WAG",   "HELLO"),
    ("PALM",  "STILL", "STOP"),
    ("THUMB", "MOVING","GOOD"),
    ("PEACE", "STILL", "PEACE"),
]

for shape, motion, expected in fusion_tests:
    result = get_word(shape, motion)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_passed = False
    print(f"  [{status}] ({shape} + {motion}) -> expected={expected}, got=      {result}")

print()
if all_passed:
    print("All tests PASSED.")
else:
    print("SOME TESTS FAILED -- check thresholds.")
