import numpy as np
import sys
sys.path.append('/home/shamshassiki/Shams_Analyzing_scripts/NuRadioMC/NuRadioMC')
import matplotlib.pyplot as plt
import os
import json
from NuRadioReco.detector.detector import Detector
from NuRadioReco.detector.RNO_G import rnog_detector
import datetime as dt
from scipy.signal import savgol_filter

db_det=rnog_detector.Detector(
    detector_file=None
    )
db_det.update(dt.datetime(2024,5,2))


stations=[24,23,22,21,14,13,12,11]

channels=[0,1,2,3]
beams=[0,1,2,3,4,5,6,7,8,9,10,11]
version="v0p18"
make_plots=True
print_for_quartus=True
save_beams=True
print_for_python=True
c=2.99792458e8
n=1.75
sampling_rate=472e6
int_factor=4
int_rate=sampling_rate*int_factor
num_antennas=4
file='RNO_season_2024.json'
det=Detector(file,source="json")

det.update(dt.datetime.now())
#det=db_det
f=np.linspace(.06,.236,10000)
phase_delays={}
print("relative group delays")
for station in stations:

    #if station==14:
    #    db_det.update(dt.datetime(2025,5,5))
    #else:
    #    db_det.update(dt.datetime(2023,8,3))

    plt.figure()
    plt.title(f"station {station}")

    f = np.linspace(.06,.236,10000)
    dts = []
    try:
        rel = db_det.get_signal_chain_response(station,0,trigger=True)(f)
    except:
        print(f"{station} not in db det for group delays")
        phase_delays[station] = dict(zip(channels,np.zeros(4)))
        continue

    for i in range(0,4):

        fmin=.15
        fmax=.2

        fs = np.linspace(.9*fmin, 1.1*fmax, 1000)
        response = db_det.get_signal_chain_response(station, i, trigger=True)(fs)
  
        phase_angle = np.angle(response)
        unwrapped = np.unwrap(phase_angle)
        group_delays = -np.gradient(unwrapped) / (2 * np.pi * np.gradient(fs))
        avg_delay = np.mean( group_delays[np.logical_and(fs>fmin, fs<fmax)] )
        dts.append(avg_delay)


        fig,ax=plt.subplots(3,1,sharex=True,figsize=(6,8))
        ax[0].plot(fs,phase_angle,label="angle")
        ax[0].set_ylabel("phase angle [rad]")
        ax[1].plot(fs,unwrapped,label="unwrapped angle")
        #ax[1].plot(f,smooth,label="smoothed angle")
        ax[1].set_ylabel("phase angle [rad]")
        ax[1].legend()
        ax[2].plot(fs,group_delays,label="group delay")
        #ax[2].plot(fs,smoothed_del,label="smoothed group delay")
        ax[2].set_xlabel("freq [GHz]")
        ax[2].set_ylabel("group delay [ns]")
        ax[2].legend()
        fig.suptitle(f"Station {station} Channels 0-{i}")
        plt.close()
        #plt.show()

    plt.ylabel("Relative Group Delay [ns]")
    plt.xlabel("Freq. [MHz]")
    plt.ylim([-5,5])
    plt.text(75,-4,f"Rel. to CH0 @ 200MHz {np.round(dts,decimals=3)} ns",fontsize=10)
    plt.legend()
    plt.close()
    #plt.savefig(f"plots/group_delay_station_{station}.png")
    plt.close()
    #plt.show()

    print(station, dts)
    dts=np.array(dts)

    phase_delays[station]=dict(zip(channels,dts))

print(phase_delays)
f=open(f"{version}_rel_group_delays.json","w")
json.dump(phase_delays,f,indent=4)

all_delays=np.zeros((len(stations),len(channels)))
all_depths=np.zeros((len(stations),len(channels)))
num_beams=12

for i in range(len(stations)):

    for j in range(len(channels)):
        
        if version=="v0p16":
            all_delays[i,j]=det.get_channel(stations[-i-1],channels[j])['cab_time_delay']
            all_depths[i,j]=det.get_channel(stations[-i-1],channels[j])['ant_position_z'] 

        if version=="v0p17":
            all_delays[i,j]=det.get_channel(stations[i],channels[j])['cab_time_delay']
            all_depths[i,j]=det.get_channel(stations[i],channels[j])['ant_position_z']  

        if version=="v0p18":
            #if stations[i]==14:
            #    db_det.update(dt.datetime(2024,2,2))
            #else:
            #    db_det.update(dt.datetime(2023,8,3))

            try:
                #database first
                all_delays[i,j]=db_det.get_cable_delay(stations[i],channels[j],trigger=True) + phase_delays[stations[i]][j]
                all_depths[i,j]=db_det.get_relative_position(stations[i],channels[j])[2]

            except:
                print("db failed")
                try:
                    #in case there's a calibrated file
                    all_delays[i,j]=db_det.get_channel(stations[i],channels[j])['cab_time_delay'] + phase_delays[stations[i]][j] 
                    all_depths[i,j]=db_det.get_channel(stations[i],channels[j])['ant_position_z']

                except:
                    #fallback 2024 json
                    all_delays[i,j]=det.get_channel(stations[i],channels[j])['cab_time_delay']
                    all_depths[i,j]=det.get_channel(stations[i],channels[j])['ant_position_z']
