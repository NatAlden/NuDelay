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
JSON_FILE = "trigger_efficiency_mode_1_no_filters.json"

# ----------------------------
# Simulated Peak-to-Peak Analysis (replace with your real logic)
# ----------------------------
RATE = 1000

def run_peak_to_peak_analysis(attenuation_percent, attenuation_scale):
    # Replace with real signal processing here
    coinc = get_coinc_rate()
    time.sleep(0.5)

    return {
        "attenuation_percent": attenuation_percent,
        "attenuation_scale": attenuation_scale,
        "coincidence_rate": coinc,
    }

# ----------------------------
# Append results to JSON
# ----------------------------
def save_report(all_reports):
    with open(JSON_FILE, 'w') as f:
        json.dump(all_reports, f, indent=2)

# ----------------------------
# Command handler
# ----------------------------
def handle_command(cmd, all_reports = None):
    commands = cmd.split(",")
    attenuation_percent = float(commands[2])
    run_name = str(commands[1])
    attenuation_scale = int(round(float(commands[0])))
    if all_reports is None:
       all_reports = []

    if attenuation_percent <= 100:
        print(f" Running attenuation scan at {attenuation_percent}%")

        report = run_peak_to_peak_analysis(attenuation_percent, attenuation_scale)
        coincidence=report["coincidence_rate"] 
        report["report_name"] = "The efficiency is "+ str(coincidence/RATE)
        #save_report(report)
        all_reports.append(report)

        reply_message = f"{report['report_name']} ran successfully"
    else:
        reply_message = "Invalid attenuation. Did not run."
        report = {}

    return all_reports, reply_message

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
            #print(f"resetting json file")
            #open(JSON_FILE, 'w').close()
            
            all_reports = None
            while True:
                data = conn.recv(1024)
                if not data:
                    save_report(all_reports)
                    break
                cmd = data.decode().strip()
                print(f"[FLOWER] Received command: {cmd}", '\n')
                time.sleep(0.01)
                all_reports, return_msg = handle_command(cmd, all_reports=all_reports)
                conn.sendall(return_msg.encode())

if __name__ == "__main__":
    main()
