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
JSON_FILE = "peak_to_peak_coinc_analysis.json"

# ----------------------------
# Simulated Peak-to-Peak Analysis (replace with your real logic)
# ----------------------------
RATE = 1000

def run_peak_to_peak_analysis(attenuation_percent, attenuation_scale):
    # Replace with real signal processing here
    coinc = get_coinc_rate()
    time.sleep(0.01)

    ptp = get_peak2peak()
    time.sleep(0.01)
    return {
        "attenuation_percent": attenuation_percent,
        "attenuation_scale": attenuation_scale,
        "coincidence_rate": coinc,
        "peak_to_peak": ptp

    }

# ----------------------------
# Append results to JSON
# ----------------------------
def save_report(report):
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            all_reports = json.load(f)
    else:
        all_reports = []

    all_reports.append(report)

    with open(JSON_FILE, 'w') as f:
        json.dump(all_reports, f, indent=2)

# ----------------------------
# Command handler
# ----------------------------
def handle_command(cmd):
    commands = cmd.split(",")
    attenuation_percent = float(commands[2])
    run_name = str(commands[1])
    attenuation_scale = int(round(float(commands[0])))


    if attenuation_percent <= 100:
        print(f" Running attenuation scan at {attenuation_percent}%")

        report = run_peak_to_peak_analysis(attenuation_percent, attenuation_scale)
        coincidence=report["coincidence_rate"] 
        report["report_name"] = "The efficiency is "+ str(coincidence/RATE)
        save_report(report)

        reply_message = f"{report["report_name"]} ran successfully"
    else:
        reply_message = "Invalid attenuation. Did not run."
        report = {}

    return attenuation_percent, run_name, reply_message, attenuation_scale

# ----------------------------
# TCP Server Loop
# ----------------------------
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"[FLOWER] Waiting for WaveSynth on port {PORT}...")

        conn, addr = s.accept()
        with conn:
            print(f"[FLOWER] Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                cmd = data.decode().strip()
                print(f"[FLOWER] Received command: {cmd}")
                time.sleep(0.001)
                atten_percent, run, return_msg, atten_scale = handle_command(cmd)
                conn.sendall(return_msg.encode())

if __name__ == "__main__":
    main()