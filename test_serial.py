import serial
import time

PORT      = "/dev/ttyACM0"
BAUD_RATE = 115200

print(f"Opening {PORT} at {BAUD_RATE} baud...")
print("Move your gloved hand -- you should see changing numbers.")
print("Press Ctrl+C to stop.\n")

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()

    sample_count = 0

    while True:
        raw_line = ser.readline()

        if not raw_line:
            print("  [timeout -- no data received]")
            continue

        try:
            decoded = raw_line.decode("utf-8").strip()
            parts   = decoded.split(",")

            if len(parts) != 6:
                continue

            ax, ay, az = float(parts[0]), float(parts[1]), float(parts[2])
            gx, gy, gz = float(parts[3]), float(parts[4]), float(parts[5])

            sample_count += 1

            if sample_count % 10 == 0:
                print(
                    f"Accel: X={ax:+.3f}g  Y={ay:+.3f}g  Z={az:+.3f}g  |  "
                    f"Gyro:  X={gx:+.1f}  Y={gy:+.1f}  Z={gz:+.1f}  deg/s"
                )

        except ValueError:
            continue

except serial.SerialException as e:
    print(f"Serial error: {e}")
    print("Is the Arduino plugged in? Is Serial Monitor closed?")

except KeyboardInterrupt:
    print(f"\nStopped. Received {sample_count} total samples.")
    ser.close()
