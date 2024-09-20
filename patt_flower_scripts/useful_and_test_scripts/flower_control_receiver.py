import socket
import time

HOST = ''
PORT = 9000

def handle_command(cmd):
    commands = cmd.split(",")
    attenuation = float(commands[0])
    run_name = str(commands[1])

    if attenuation <= 100:
        print("Running attenuation scan at", str(attenuation), "%")
        #run line for finding PtP here

        reply_message = f"{run_name} ran successfully"

    else:
        reply_message = 'did not run'


    return attenuation, run_name, reply_message

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
                atten, run, return_msg = handle_command(cmd)
                conn.sendall(return_msg.encode())  # Encode the string for transmission

if __name__ == "__main__":
    main()

