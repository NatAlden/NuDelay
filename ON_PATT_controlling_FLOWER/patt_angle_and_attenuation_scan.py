import time
import serial
import socket
import numpy as np
from typing import List
from attenuation_control import apply_attenuation_to_all_channels

# === Parameters ===
in_angles = np.arange(-60,60, 0.5)  # degrees
attenuation_codes = np.arange(40, 105, 2)  # DAC values for attenuation (0–127)
calibration_delays = [5.19, 0, 5.21, 6.08]  #[5.35, 0, 5.3, 6.35]  # per-channel fixed delay offsets (ns)

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

# === Network settings ===
FLOWER_IP = "10.42.1.228"
PORT = 9000


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

def apply_delay_preset(delays_ns: List[float]) -> None:
    for ch, delay_ns in zip(CHANNEL_ORDER, delays_ns):
        cmd = f"{CHANNEL_MAP[ch]}D {round(delay_ns,3)}n"
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
    print("[RUN ] Connecting to FLOWER and beginning scan…\n")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((FLOWER_IP, PORT))
        print(f"[NET ] Connected to FLOWER @ {FLOWER_IP}:{PORT}")

        for i, delay_set in enumerate(delay_list):
            angle = in_angles[i]
            print(f"\n[STEP] Angle {angle:+05.1f}° → delays = {delay_set} (ns)")
            apply_delay_preset(delay_set)

            for att_code in attenuation_codes:
                pct = apply_attenuation_to_all_channels(att_code)
                time.sleep(2)

                run_name = f"ang{angle:+05.1f}_att{att_code:06.2f}"
                msg = f"{angle},{att_code},{pct:.2f},{run_name}"
                sock.sendall(msg.encode())

                reply = sock.recv(1024).decode().strip()
                print(f"  ↳ att {att_code:6.2f} (≈{pct:6.2f}%): {reply}")

    print("\n[DONE] Full scan finished.")
    ser.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ABORT] Scan interrupted by user.")
        ser.close()
