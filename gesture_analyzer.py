STILL_GYRO_MAX    = 20.0
STILL_ACCEL_RANGE = 0.25
PUNCH_ACCEL_RANGE = 0.8
WAG_ACCEL_RANGE   = 0.55
TWIST_GYRO_MIN    = 150.0
MIN_SAMPLES       = 15

def analyze(snapshot):
    if len(snapshot) < MIN_SAMPLES:
        return "NO_DATA"

    ax_vals = [s[1] for s in snapshot]
    ay_vals = [s[2] for s in snapshot]
    gx_vals = [s[4] for s in snapshot]
    gy_vals = [s[5] for s in snapshot]
    gz_vals = [s[6] for s in snapshot]

    ax_range      = max(ax_vals) - min(ax_vals)
    ay_range      = max(ay_vals) - min(ay_vals)
    peak_gx       = max(abs(v) for v in gx_vals)
    peak_gy       = max(abs(v) for v in gy_vals)
    peak_gz       = max(abs(v) for v in gz_vals)
    peak_gyro_any = max(peak_gx, peak_gy, peak_gz)

    # STILL
    if (peak_gyro_any < STILL_GYRO_MAX
            and ax_range < STILL_ACCEL_RANGE
            and ay_range < STILL_ACCEL_RANGE):
        return "STILL"

    # PUNCH: ax dominates accel
    if ax_range > PUNCH_ACCEL_RANGE and ax_range > ay_range:
        return "PUNCH"

    # TWIST: gx is the dominant axis for wrist rotation
    # on this specific glove mounting orientation
    # Threshold 150 is safely above wag noise (gx ~50-80 during wag)
    # but well below twist signal (gx 500-726 during twist)
    if peak_gx > TWIST_GYRO_MIN and peak_gx > peak_gy and peak_gx > peak_gz:
        return "TWIST"

    # WAG: ay dominates accel
    if ay_range > WAG_ACCEL_RANGE and ay_range > ax_range:
        return "WAG"

    return "MOVING"

def get_word(shape, motion):
    fusion_table = {
        ("INDEX", "PUNCH") : "YOU",
        ("INDEX", "WAG")   : "NO",
        ("INDEX", "STILL") : "ONE",
        ("PALM",  "TWIST") : "MINE",
        ("PALM",  "WAG")   : "HELLO",
        ("PALM",  "STILL") : "STOP",
        ("THUMB", "STILL") : "GOOD",
        ("THUMB", "MOVING"): "GOOD",
        ("THUMB", "PUNCH") : "GOOD",
        ("THUMB", "WAG")   : "GOOD",
        ("THUMB", "TWIST") : "GOOD",
        ("PEACE", "STILL") : "PEACE",
        ("PEACE", "MOVING"): "PEACE",
        ("PEACE", "PUNCH") : "PEACE",
        ("PEACE", "WAG")   : "PEACE",
        ("PEACE", "TWIST") : "PEACE",
    }
    return fusion_table.get((shape, motion), None)