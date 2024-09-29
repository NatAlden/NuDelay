
import time
import serial
import numpy as np
from typing import List
from attenuation_control import apply_attenuation_to_all_channels

# === Parameters ===
in_angles = np.arange(-10, 11, 5)  # degrees
attenuation_codes = np.arange(0, 21, 4)  # DAC values for attenuation (0–127)
calibration_delays = [4.9, 0.1, 4.78, 6.3]  # per-channel fixed delay offsets (ns)

# === Channel/serial setup ===
CHANNEL_MAP = {"C1": "A", "C2": "B", "C3": "C", "C4": "D"}
CHANNEL_ORDER: List[str] = ["C1", "C2", "C3", "C4"]

ser = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=38400,
    timeout=1,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)
ser.close(); ser.open()

# === Physics ===
n_ice= 1.78  #index of refraction in ice
vertical_seperation= 1 #distance betwwen channel in meters
channel_weights= [1,1,1,1] #the weight attributed to each channel
c= 299792458 #speed of light in a vaccum in m/s

def angle_delay_time(index, distance, speed, angle ):
    angle=np.deg2rad(angle)

    #this is the offset in time of each signal that is generated
    time_delays= index * distance * np.sin(angle) / speed
    return time_delays*1e9

def send(cmd: str, loud: bool = True) -> str:
    ser.write((cmd + "\n").encode())
    resp = ser.readline().decode().strip()
    if loud:
        print(f"[SERIAL] {cmd} → {resp}")
    return resp

def apply_delay_preset(delays_ns: List[int]) -> None:
    for ch, delay_ns in zip(CHANNEL_ORDER, delays_ns):
        cmd = f"{CHANNEL_MAP[ch]}D {delay_ns}n"
        send(cmd)
    send("DW 2u")
    send("DSET")
    for ch in CHANNEL_ORDER:
        send(f"{CHANNEL_MAP[ch]}SET")
    time.sleep(0.3)

# === Precompute all delay sets ===
delay_list = []
for angle in in_angles:
    delays = angle_delay_time(n_ice, vertical_seperation, c, angle)
    step_delay = abs(delays)
    base_delays = [round(i * step_delay, 2) for i in range(4)]
    if delays < 0:
        base_delays = base_delays[::-1]
    delays_ns = [base_delays[i] + calibration_delays[i] for i in range(4)]
    delay_list.append(delays_ns)

# === Main loop ===
def main():
    print("[RUN ] Beginning local scan (no FLOWER connection)…\n")

    for i, delay_set in enumerate(delay_list):
        angle = in_angles[i]
        print(f"\n[STEP] Angle {angle:+05.1f}° → delays = {delay_set} (ns)")
        apply_delay_preset(delay_set)

        for att_code in attenuation_codes:
            pct = apply_attenuation_to_all_channels(att_code)
            time.sleep(2.5)

            run_name = f"ang{angle:+05.1f}_att{att_code:06.2f}"
            print(f"  ↳ att {att_code:6.2f} (≈{pct:6.2f}%): {run_name}")

    print("\n[DONE] Local scan finished.")
    ser.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ABORT] Scan interrupted by user.")
        ser.close()

