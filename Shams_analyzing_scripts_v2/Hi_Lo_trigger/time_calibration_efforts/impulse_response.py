import json
import numpy as np
import csv
from scipy import signal
import matplotlib.pyplot as plt
import tools.waveform as waveform
import tools.myplot
import vpol_txrx as rxtx


RADIANT_SAMPLING_RATE = 2.400
RADIANT_SAMPLING_RATE_2023 = 3.200

FLOWER_SAMPLING_RATE = 0.472
UPSAMPLE_FACTOR=40

directory = "/mnt/labdata/chicago-rnog-system-response-2024/lab_measurements/labdata/"
filename=[]
## DEEP full-chain files
filename.append("fullchain_deep_channel2_lowthreshon_fastimpulse.json")
filename.append("fullchain_deep_channel2_lowthreshon_fastimpulse+6dB.json")
filename.append("fullchain_deep_channel9_lowthreshon_fastimpulse+6dB.json")
filename.append("fullchain_deep_channel11_lowthreshon_fastimpulse+6dB.json")

## SURFACE full-chain files
filename.append("amps40dB_surface_channel_13.json")
filename.append("amps46dB_surface_channel13.json")
filename.append("amps40dB_surface_channel14.json")
filename.append("amps46dB_surface_channel14.json")

##RADIANT only data
filename.append("deep_channel10.json")


def make_avg_wf(wave_list, upsamp=UPSAMPLE_FACTOR, method='cor'):

    average_wf = wave_list[0]
    average_wf.fft()
    average_wf.upsampleFreqDomain(upsamp)

    for wave in wave_list[1:]:
        wave.fft()
        wave.upsampleFreqDomain(upsamp)
        if method=='cor':
            cor = wave.crossCorrelate(average_wf)
            delay=int(np.argmax((cor))-np.size(cor)/2.)
        else:
            delay=int(np.argmax((wave.voltage))-np.size(wave.voltage)/2.)

        wave.voltage = np.roll(wave.voltage,-delay)
        average_wf.voltage += wave.voltage

    average_wf.voltage = average_wf.voltage / float(len(wave_list))
    return average_wf

def load_and_list_radiant_wfs(filename, amplitude_thresh_for_processing=180, verbose=True):

    with open(filename, "r") as run:
        data = json.load(run)
    wfs = []
    n_null=0
    
    for idx, ev in enumerate(data):
    
        if  (np.max(np.abs((ev["radiant_waveforms"]))) > amplitude_thresh_for_processing) and \
            (np.argmax(np.abs((ev["radiant_waveforms"]))) > 40) and \
            (np.argmax(np.abs((ev["radiant_waveforms"]))) <2000): 
            wfs.append(waveform.Waveform(ev["radiant_waveforms"], sampling_rate=1./RADIANT_SAMPLING_RATE))
        else:
            n_null += 1
    if verbose:
        print(filename, len(wfs))

    return wfs

def load_and_list_radiant_wfs_ryan(filename, amplitude_thresh_for_processing=180, ch=0, evt_list=[100,120], verbose=True):

    with open(filename, "r") as run:
        data = json.load(run)
    wfs = []
    n_null=0
    for idx in range(len(data)-2):

        _wave=data[str(idx)][str(ch)]

        if idx >= evt_list[0] and idx <= evt_list[1] and \
           (np.max(_wave) > amplitude_thresh_for_processing) and \
           (np.argmax(_wave) > 40) and \
           (np.argmax(_wave) <2000): 
            wfs.append(waveform.Waveform(_wave, sampling_rate=1./RADIANT_SAMPLING_RATE))
        else:
            n_null += 1
    if verbose:
        print(filename, len(wfs))

    return wfs

def load_and_list_flower_wfs(filename, amplitude_thresh_for_processing=10, ch='ch2', verbose=True):

    with open(filename, "r") as run:
        data = json.load(run)
    wfs = []
    n_null=0

    for idx in range(len(data['events'])):

        _wave=data['events'][idx][ch][0:512]
                            
        if  (np.max(_wave) > amplitude_thresh_for_processing) and \
            (np.argmax(np.abs(_wave)) > 30) and \
            (np.argmax(np.abs(_wave)) <480): 
            wfs.append(waveform.Waveform(_wave, sampling_rate=1./FLOWER_SAMPLING_RATE))
        else:
            n_null += 1
    if verbose:
        print(filename, len(wfs))

    return wfs

def center_waveform(wave, index=None):
    if index==None:
        _wave = np.roll(wave, -int(np.argmin(wave)-len(wave)/2))
    else:
        _wave = np.roll(wave, -int(np.argmin(wave)-int(index)))
    return _wave

def loadFieldFoxCSV(filename):
	data = np.loadtxt(filename, comments='E', delimiter=',',skiprows=17)
	return data

if __name__ == "__main__":

    avg_impulse_response=[]
    for f in filename:
        if f=="deep_channel10.json":
            wfs = load_and_list_radiant_wfs(directory+f, 50)
        else:
            wfs = load_and_list_radiant_wfs(directory+f)

        #plt.plot(wfs[0].time, wfs[0].voltage, color='black', lw=1)
        average_impulse = make_avg_wf(wfs, method='')
        #plt.plot(average_impulse.time, average_impulse.voltage, color='red', lw=1)

        ####center average waveform in window
        average_impulse.voltage = np.roll(average_impulse.voltage,
                                          -int(np.argmax(average_impulse.voltage)-len(average_impulse.voltage)/2))
        avg_impulse_response.append(average_impulse)

    deep_ir = {}
    deep_ir['time'] = avg_impulse_response[0].time.tolist()
    deep_ir['ch2_2x_amp'] = (avg_impulse_response[0].voltage/ (np.max(avg_impulse_response[0].voltage))).tolist()
    deep_ir['ch2'] = (avg_impulse_response[1].voltage/ (np.max(avg_impulse_response[1].voltage))).tolist()
    deep_ir['ch9'] = (avg_impulse_response[2].voltage/ (np.max(avg_impulse_response[2].voltage))).tolist()
    deep_ir['ch10'] = (avg_impulse_response[3].voltage/ (np.max(avg_impulse_response[3].voltage))).tolist()
    with open('deep_impulse_responses.json', 'w') as json_file:
        json.dump(deep_ir, json_file)

    surf_ir = {}
    surf_ir['time'] = avg_impulse_response[4].time.tolist()
    surf_ir['ch13_2x_amp'] = (avg_impulse_response[4].voltage/ (np.max(avg_impulse_response[4].voltage))).tolist()
    surf_ir['ch13'] = (avg_impulse_response[5].voltage/ (np.max(avg_impulse_response[5].voltage))).tolist()
    surf_ir['ch14_2x_amp'] = (avg_impulse_response[6].voltage/ (np.max(avg_impulse_response[6].voltage))).tolist()
    surf_ir['ch14'] = (avg_impulse_response[7].voltage/ (np.max(avg_impulse_response[7].voltage))).tolist()
    with open('surface_impulse_responses.json', 'w') as json_file:
        json.dump(surf_ir, json_file) 

    ##PLOT DEEP IR's
    t0=427.0
    plt.figure()
    plt.plot(avg_impulse_response[0].time-t0, avg_impulse_response[0].voltage / (np.max(avg_impulse_response[0].voltage)), color='blue', lw=1, label='RADIANT ch2 2x amplitude')
    plt.plot(avg_impulse_response[1].time-t0, avg_impulse_response[1].voltage / (np.max(avg_impulse_response[1].voltage)), color='skyblue', lw=1, label='RADIANT ch2')
    plt.plot(avg_impulse_response[2].time-t0, avg_impulse_response[2].voltage / (np.max(avg_impulse_response[2].voltage)), color='black', lw=1, label='RADIANT ch9')
    plt.plot(avg_impulse_response[3].time-t0, avg_impulse_response[3].voltage / (np.max(avg_impulse_response[3].voltage)), color='maroon', lw=1, label='RADIANT ch10')
    plt.legend(loc='upper right')
    plt.xlim([-10, 45])
    plt.xlabel('time [ns]')
    plt.ylabel('amplitude [norm]')
    #plt.title('Impulse Response Full Deep Signal Chain')
    plt.tight_layout()

    fig, ax = plt.subplots(2,1)
    for i in range(4):
        test_response = avg_impulse_response[i]
        test_response.medianSubtract()
        #ax[0].plot(test_response.voltage)
        test_response.voltage = rxtx.window(test_response.voltage, 20000)
        test_response.voltage[0:np.where(test_response.time > 415)[0][0]] = 0.0
        print(np.where(test_response.time > 400)[0][0])
        ax[0].plot(avg_impulse_response[i].time, test_response.voltage, label=str(i))
        ax[0].set_xlabel('time [ns]')
        ax[0].set_ylabel('amplitude')
        ax[0].set_xlim([400,600])
        #ax[0].tight_layout()
        
        test_response.fft()
        print (np.max(np.abs(test_response.ampl)))
        ax[1].plot(test_response.freq, np.abs(test_response.ampl)/(np.max(np.abs(test_response.ampl[100:]))-5000), label=str(i))
        ax[1].set_xlabel('freq [GHz]')
        ax[1].set_xlim([0,1])
        ax[1].legend(loc='upper right')
        ax[0].legend(loc='upper left')
        #plt.ylim([-30,5])
        
        ax[1].set_ylabel('ampl')
        #ax[1].tight_layout()

    s21_icrc = loadFieldFoxCSV('/home/ejo/icrc_23_measurements/1.csv')
    linear_gain = np.abs(np.power(10,(s21_icrc[:,1]+40.)/20))
    ax[1].plot(s21_icrc[:,0] * 1.e-9, linear_gain/np.max(linear_gain), label='downhole chain', c='black', lw=2)

    ax[0].set_title('deep-chain response, compared to VNA [black-curve, bottom]')
    plt.tight_layout()
    plt.show()
    
    t0=426.0
    plt.figure()
    plt.plot(avg_impulse_response[4].time-t0, avg_impulse_response[4].voltage / np.abs((np.min(avg_impulse_response[4].voltage))), color='blue', lw=1, label='RADIANT ch13 2x amp.')
    plt.plot(avg_impulse_response[5].time-t0, avg_impulse_response[5].voltage / np.abs((np.min(avg_impulse_response[5].voltage))), color='skyblue', lw=1, label='RADIANT ch13')
    plt.plot(avg_impulse_response[6].time-t0, avg_impulse_response[6].voltage / np.abs((np.min(avg_impulse_response[6].voltage))), color='black', lw=1, label='RADIANT ch14 2x amp.')
    plt.plot(avg_impulse_response[7].time-t0, avg_impulse_response[7].voltage / np.abs((np.min(avg_impulse_response[7].voltage))), color='maroon', lw=1, label='RADIANT ch14')
    plt.legend(loc='upper right')
    plt.xlim([-10, 55])
    plt.xlabel('time [ns]')
    plt.ylabel('amplitude [norm]')
    #plt.title('Impulse Response Full Deep Signal Chain')
    plt.tight_layout()
    plt.show()
    
    ##
