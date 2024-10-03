
import socket
import time
import json
import os
from datetime import datetime
import sys
sys.path.append("/home/rno-g/flowerpy")

from utils import get_peak2peak, get_coinc_rate

HOST = ''
PORT = 9000
JSON_FILE = "Full_scan_2Filters_08_01_plane_HiLo.json"
RATE = 1000  # normalization constant

def run_peak_to_peak_analysis(angle_deg, att_code, percent):
    coinc = get_coinc_rate()
    time.sleep(0.5)

    return {
        "angle_deg": angle_deg,
        "attenuation_code": att_code,
        "attenuation_percent": percent,
        "coincidence_rate": coinc,
        "efficiency": coinc / RATE
    }

def save_report(results):
    with open(JSON_FILE, 'w') as f:
        json.dump(results, f, indent=2)

def handle_command(cmd, reports=None):
    if reports is None:
        reports = []

    try:
        angle_deg, att_code, percent, run_name = cmd.strip().split(',')
        angle_deg = float(angle_deg)
        att_code = float(att_code)
        percent = float(percent)

        print(f"[RUN ] angle {angle_deg}°, att_code {att_code}, {percent:.1f}%")

        report = run_peak_to_peak_analysis(angle_deg, att_code, percent)
        report["run_name"] = run_name
        reports.append(report)

        reply = f"Efficiency = {report['efficiency']:.4f} recorded"

    except Exception as e:
        reply = f"[ERROR] Failed to parse or run: {e}"
        print(reply)

    return reports, reply

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"[FLOWER] Waiting on port {PORT} …")

        conn, addr = s.accept()
        with conn:
            print(f"[FLOWER] Connected by {addr}")
            reports = []
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                cmd = data.decode().strip()
                reports, msg = handle_command(cmd, reports)
                conn.sendall(msg.encode())

            save_report(reports)
            print("[FLOWER] Scan complete. Results saved.")

if __name__ == "__main__":
    main()

