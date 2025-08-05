import numpy as np
import time
import serial

# === Constants and Calibration ===
n_ice = 1.78  # index of refraction in ice
vertical_seperation = 1  # meters
c = 299792458  # m/s (speed of light)
calibration_delays = [5.40, 0, 5.34, 6.04]  # ns

# === Channel Mapping ===
CHANNEL_MAP = {"C1": "A", "C2": "B", "C3": "C", "C4": "D"}
CHANNEL_ORDER = ["C1", "C2", "C3", "C4"]

# === Serial Setup ===
ser = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=38400,
    timeout=1,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)
ser.close(); ser.open()

def send(cmd: str, loud: bool = True) -> str:
    ser.write((cmd + "\n").encode())
    resp = ser.readline().decode().strip()
    if loud:
        print(f"[SERIAL] {cmd} → {resp}")
    return resp

def angle_delay_time(n, d, c, angle_deg):
    angle_rad = np.deg2rad(angle_deg)
    delay = n * d * np.sin(angle_rad) / c
    return -delay * 1e9  # ns #because ch3 is on top and ch0 is at the bottom this is to flip th order of the delays

def apply_delay_preset(delays_ns):
    for ch, delay_ns in zip(CHANNEL_ORDER, delays_ns):
        cmd = f"{CHANNEL_MAP[ch]}D {round(delay_ns, 3)}n"
        send(cmd)
    send("DW 2u")
    send("DSET")
    for ch in CHANNEL_ORDER:
        send(f"{CHANNEL_MAP[ch]}SET")
    time.sleep(0.3)

# === Main Script ===
def main():
    try:
        angle = float(input("Enter incident angle (between -90 and 90 degrees): "))
        if not -90 <= angle <= 90:
            raise ValueError("Angle out of range.")

        delays = angle_delay_time(n_ice, vertical_seperation, c, angle)
        step_delay = abs(delays)
        base_delays = [round(i * step_delay, 2) for i in range(4)]
        if delays < 0:
            base_delays = base_delays[::-1]
        final_delays = [base_delays[i] + calibration_delays[i] for i in range(4)]

        print(f"Applying delays for angle {angle:+.2f}° → {final_delays} ns")
        apply_delay_preset(final_delays)

    except ValueError as e:
        print(f"Error: {e}")
    finally:
        ser.close()

if __name__ == "__main__":
    main()

