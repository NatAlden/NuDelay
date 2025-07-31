import socket
import time

FLOWER_IP = '10.42.1.228'  # Replace with actual IP of FLOWER board
PORT = 9000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((FLOWER_IP, PORT))
    print("[WaveSynth] Connected to FLOWER")

    for i in range(100):
        msg= str(int(100-i))
        s.sendall(msg.encode())
        time.sleep(0.5)
        data = s.recv(1024)
        print("[WaveSynth] Got back:", data.decode())

