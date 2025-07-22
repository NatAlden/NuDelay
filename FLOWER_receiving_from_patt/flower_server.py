import socket

HOST = ''         # Listen on all interfaces
PORT = 9000       # Arbitrary port number

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"[FLOWER] Listening on port {PORT}...")
    conn, addr = s.accept()
    with conn:
        print(f"[FLOWER] Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print("[FLOWER] Received:", data.decode())
            conn.sendall(b"ACK")

