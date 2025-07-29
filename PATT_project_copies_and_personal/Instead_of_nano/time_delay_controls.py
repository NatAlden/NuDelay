import time
import serial
from typing import List
import numpy as np

in_angles=np.arange(-10, 11, 5)  # angles in degrees
calibration_delays= [4.9, 0.1, 4.78, 6.3]  # delays in ns for each channel

# === Channel/serial setup ===
CHANNEL_MAP   = {"C1": "A", "C2": "B", "C3": "C", "C4": "D"}  # REVERSED mapping
CHANNEL_ORDER: List[str] = ["C1", "C2", "C3", "C4"]

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

def apply_delay_preset(delays_ns: List[int]) -> None:
    for ch, delay_ns in zip(CHANNEL_ORDER, delays_ns):
        cmd = f"{CHANNEL_MAP[ch]}D {delay_ns}n"
        send(cmd)
    send("DW 2u")
    send("DSET")
    for ch in CHANNEL_ORDER:
        send(f"{CHANNEL_MAP[ch]}SET")
    time.sleep(0.3)

n_ice= 1.78  #index of refraction in ice
vertical_seperation= 1 #distance betwwen channel in meters
channel_weights= [1,1,1,1] #the weight attributed to each channel
c= 299792458 #speed of light in a vaccum in m/s

def angle_delay_time(index, distance, speed, angle ):
    angle=np.deg2rad(angle)

    #this is the offset in time of each signal that is generated
    time_delays= index * distance * np.sin(angle) / speed
    return time_delays*1e9

delay_list = []
for angle in in_angles:
    delays = angle_delay_time(n_ice, vertical_seperation, c, angle)
    step_delay = abs(delays)
    base_delays = [round(i * step_delay, 2) for i in range(4)]
    if delays < 0:
        base_delays = base_delays[::-1]
    delays_ns = [base_delays[i] + calibration_delays[i] for i in range(4)]
    delay_list.append(delays_ns)


def main():

    print("[RUN ] Applying preset delay sets…")
    for i, delay_set in enumerate(delay_list):
        print(f"\n[STEP] Delay set {i+1}: {delay_set} (ns)")
        apply_delay_preset(delay_set)

    ser.close()
    print("\n[DONE] All delay sets applied.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ABORT] Test interrupted."); ser.close()