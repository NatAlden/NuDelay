import json
import numpy as np
import csv
from scipy import signal
import matplotlib.pyplot as plt
import tools.waveform as waveform
import tools.myplot
import tools.read_tektronix as read_tek

UPSAMPLE_FACTOR=50

pulse_directory = "/mnt/labdata/chicago-rnog-system-response-2024/anechoic_chamber_PSL/2024_10_08/03_VpolTx_VpolRx/"
cable_cal_directory = "/mnt/labdata/chicago-rnog-system-response-2024/anechoic_chamber_PSL/2024_10_08/05_COAX_VNA/"

tx_cable_file = 'TX_COAX_4001_RECAL.s2p'
rx_cable_file = 'RX_COAX_4001_RECAL.s2p'

tx_waveform_file = 'VpolTx_VpolRx_FARSPEC_Ch1.csv'
rx_waveform_file = 'VpolTx_VpolRx_FARSPEC_Ch2.csv'

def loadFieldFoxS21(filename):
    '''
    load s2p file
    '''
    data = np.loadtxt(filename, delimiter='\t' ,skiprows=13, dtype=str)
    freqs = np.array(data[:,0],dtype=np.float) * 1.e-9
    mag = np.power(10., np.array(data[:,3],dtype=np.float)/20.) #linear amplitude
    phase = np.array(data[:,4],dtype=np.float)
    complex_response = np.multiply(mag, np.exp(1j*np.radians(phase)))
    return freqs, complex_response

def window(wave, length):
    hanning_window = np.hanning(length)
    idx = np.argmax(wave)
    wave_windowed = np.multiply(np.concatenate((np.zeros(int(idx-length/2)), hanning_window,
                                                np.zeros(len(wave)-int(idx+length/2)))),
                                wave)
    return wave_windowed

def cable_response(factor=4):
    freqstx, tx_cable_complex_response = loadFieldFoxS21(cable_cal_directory+tx_cable_file)
    freqsrx, rx_cable_complex_response = loadFieldFoxS21(cable_cal_directory+rx_cable_file)

    ## it turns out there is exactly a factor of 4 in the frequency sampling between the
    ## VNA data and the scope sampling rate for the data processed in this file __main__
    freqstx = freqstx[::factor] #->1Mhz bins
    freqsrx = freqsrx[::factor] #->1MHz bins
    tx_cable_complex_response = tx_cable_complex_response[::4]
    rx_cable_complex_response = rx_cable_complex_response[::4]
    return freqstx, tx_cable_complex_response, rx_cable_complex_response
    
def get_heff(tx_wave, rx_wave, show=True, window_heff=True, save=True, sampling_rate=0.5):

    tx_wave.fft()
    tx_wave.timeDerivative()
    #tx_dt_wave = waveform.Waveform(np.gradient(tx_cable_convolve_wave.voltage), tx_cable_convolve_wave.time)
    tx_dt_wave = waveform.Waveform(tx_wave.voltage, tx_wave.time)
    tx_dt_wave.fft()
    #print(np.where(tx_dt_wave.ampl == 0))
    #print(tx_dt_wave.freq[1002])
    #tx_dt_wave.ampl[1002] = 0.1 #dumb hack to prevent division from failing
    rx_wave.fft()
    h_eff = np.zeros(len(rx_wave.ampl), dtype=np.complex128)

    print(len(rx_wave.ampl))
    plt.figure()
    #plt.plot(tx_wave.voltage)
    #plt.plot(rx_wave.voltage)
    plt.plot(rx_wave.freq, np.abs(rx_wave.ampl))
    plt.plot(tx_wave.freq, np.abs(tx_wave.ampl))
    plt.plot(tx_dt_wave.freq, np.abs(tx_dt_wave.ampl))

    for i in range(40,len(h_eff)-400): #exluding edge (outta band) regions where divide-by-small-number is an issue
        if abs(rx_wave.ampl[i]) < 1.0e-3 or np.abs(tx_dt_wave.ampl[i]) < 1.0e-3:
        #if abs(rx_wave.ampl[i]) < 0.06 or np.abs(tx_dt_wave.ampl[i]) < 0.5:

            h_eff[i] = 0.0
        else:
            h_eff[i] = np.divide(rx_wave.ampl[i], tx_dt_wave.ampl[i])

    
    ##h_eff is really h_eff * h_eff (2 copies), so take sqrt
    heff_theta = np.divide(np.unwrap(np.angle(h_eff)),2.0) #radians
    heff_r = np.sqrt(np.abs(h_eff)) * 1./10.*1./2*np.pi #dumb normalization to keep things sane
    heff = np.multiply(heff_r, np.exp(1j*heff_theta))
    ##load into waveform class, even though not really a waveform. useful for doing things
    heff_rx = waveform.Waveform(1 / 2.0 * np.fft.irfft(heff), sampling_rate=sampling_rate)
    heff_rxtx = waveform.Waveform(1 / 2.0 * np.fft.irfft(h_eff), sampling_rate=sampling_rate)
    plt.figure()
    plt.plot(np.abs(h_eff))
    #plt.show()

    if window_heff:
        w_len = 150
        heff_rx.voltage = window(heff_rx.voltage,w_len)

        w_len = 320
        heff_rxtx.voltage = window(heff_rxtx.voltage,w_len)

    heff_rx.fft()
    heff_rxtx.fft()

    if save:
        heff_json_save = {}
        heff_json_save['time'] = heff_rx.time.tolist()
        heff_json_save['heff_rx'] = heff_rx.voltage.tolist() #single antenna
        heff_json_save['heff_rxtx'] = heff_rxtx.voltage.tolist() #rx-tx pair (useful for anechoic setup)
        with open('heff_anechoic.json', 'w') as json_file:
            json.dump(heff_json_save, json_file)
    
    if show:
        #plt.figure()
        #plt.plot(np.abs(tx_dt_wave.ampl))
        #plt.plot(np.abs(rx_wave.ampl))
        fig, ax = plt.subplots(2,1)
        ax[0].plot(heff_rx.time, heff_rx.voltage)
        ax[0].plot(heff_rxtx.time, heff_rxtx.voltage)
        #ax[0].set_xlim([75,325])
        print(heff_rx.freq, sampling_rate)
        ax[1].plot(heff_rx.freq, np.abs(heff_rx.ampl))
        ax[1].plot(heff_rxtx.freq, np.abs(heff_rxtx.ampl))
        plt.show()

    
if __name__ == "__main__":
    
    freqstx, tx_cable_complex_response, rx_cable_complex_response = cable_response()

    tx_wave = read_tek.read_scope_cvs(pulse_directory+tx_waveform_file)
    tx_waveform = waveform.Waveform(tx_wave[1]-np.median(tx_wave[1]), tx_wave[0])
    tx_waveform.fft()

    freq_index_start = np.where(tx_waveform.freq > freqstx[0])[0][0]
    freq_index_start=3
    tx_cable_convolve_amplitudes = np.zeros(freq_index_start + len(freqstx), dtype=np.complex128)    
    tx_cable_convolve_amplitudes = tx_waveform.ampl[:freq_index_start+len(freqstx)]
    tx_cable_convolve_amplitudes[freq_index_start:] = tx_cable_convolve_amplitudes[freq_index_start:] * np.abs(tx_cable_complex_response)
    ##
    tx_cable_convolve_wave = waveform.Waveform(1 / 2.0 * 1/ 10.0 *  np.fft.irfft(tx_cable_convolve_amplitudes), sampling_rate=0.5)
    ##
    rx_wave = read_tek.read_scope_cvs(pulse_directory+rx_waveform_file)
    rx_waveform = waveform.Waveform(rx_wave[1]-np.median(rx_wave[1]), rx_wave[0])
    rx_waveform.fft()

    rx_cable_convolve_amplitudes = np.zeros(freq_index_start + len(freqstx), dtype=np.complex128)    
    rx_cable_convolve_amplitudes = rx_waveform.ampl[:freq_index_start+len(freqstx)]
    rx_cable_convolve_amplitudes[freq_index_start:] = rx_cable_convolve_amplitudes[freq_index_start:] * 1./np.abs(rx_cable_complex_response)
    ##
    rx_cable_deconvolve_wave = waveform.Waveform(1 / 2.0 * 1/ 10.0 *  np.fft.irfft(rx_cable_convolve_amplitudes), sampling_rate=0.5)
    ##
    #plt.figure()
    #plt.plot(tx_cable_convolve_wave.time-200, tx_cable_convolve_wave.voltage)
    #plt.plot(tx_waveform.time, tx_waveform.voltage)
    #plt.figure()
    #plt.plot(rx_cable_deconvolve_wave.time-200, rx_cable_deconvolve_wave.voltage)
    #plt.plot(rx_waveform.time, rx_waveform.voltage)
    ##

    fig, ax = plt.subplots(2,1)
    #ax[0].plot(tx_cable_convolve_wave.time, tx_cable_convolve_wave.voltage)
    #ax[1].plot(rx_cable_deconvolve_wave.time, rx_cable_deconvolve_wave.voltage)
    ax[0].plot(tx_waveform.time, tx_waveform.voltage)
    ax[1].plot(rx_waveform.time, rx_waveform.voltage)  
    #w_len = 80
    #tx_cable_convolve_wave.voltage = window(tx_cable_convolve_wave.voltage, w_len)
    tx_waveform.voltage = window(tx_waveform.voltage, 1000)
    
    #w_len = 320
    #rx_cable_deconvolve_wave.voltage = window(rx_cable_deconvolve_wave.voltage, w_len)
    rx_waveform.voltage = window(rx_waveform.voltage, 2900)

    
    #ax[0].plot(tx_cable_convolve_wave.time, tx_cable_convolve_wave.voltage)
    #ax[1].plot(rx_cable_deconvolve_wave.time, rx_cable_deconvolve_wave.voltage)
    ax[0].plot(tx_waveform.time, tx_waveform.voltage)
    ax[1].plot(rx_waveform.time, rx_waveform.voltage)

    #get_heff(tx_cable_convolve_wave, rx_cable_deconvolve_wave)
    print(tx_waveform.dt, rx_waveform.dt)
    #get_heff(tx_waveform, rx_waveform, sampling_rate=tx_waveform.dt)
    get_heff(tx_cable_convolve_wave, rx_cable_deconvolve_wave, sampling_rate=rx_cable_deconvolve_wave.dt)
