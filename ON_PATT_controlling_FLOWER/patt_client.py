import socket

FLOWER_IP = '10.42.1.228'  # Replace with actual IP of FLOWER board
PORT = 9000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((FLOWER_IP, PORT))
    print("[WaveSynth] Connected to FLOWER")

    while True:
        msg = input("Enter message to send to FLOWER: ")
        s.sendall(msg.encode())
        data = s.recv(1024)
        print("[WaveSynth] Got back:", data.decode())

