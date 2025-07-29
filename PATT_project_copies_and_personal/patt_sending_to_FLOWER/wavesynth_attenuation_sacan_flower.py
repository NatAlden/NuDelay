import socket
import numpy as np
import time
from attenuation_control import apply_attenuation_to_all_channels

FLOWER_IP = '10.42.1.228'  # Replace with actual IP of FLOWER board
PORT = 9000

#attenuations= np.append(np.arange(0,15,0.1) ,np.arange(15,100.01,0.5))
attenuations= np.arange(20,105.01,3)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((FLOWER_IP, PORT))
    print("[WaveSynth] Connected to FLOWER")

    for att in attenuations:
        attenuation_percent= apply_attenuation_to_all_channels(att)
        time.sleep(3.5)

        run_name="attenuation at "+str(att)+"-> "+str(attenuation_percent)+ " %"
        msg= str(att)+"," +run_name + ","+str(attenuation_percent)

        s.sendall(msg.encode())
        #time.sleep(0.1) #add to this a condition to wait for the response 

        data = s.recv(1024)
        print("[WaveSynth] Got back:", data.decode(),'\n')
