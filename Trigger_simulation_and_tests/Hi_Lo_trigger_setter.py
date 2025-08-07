import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
import math
import time
import random
import json
from pathlib import Path

#parameters
SAMPLING_RATE   =  0.472            # GHz   (0.472 GS/s)
TIME_STEP       = 1.0 / SAMPLING_RATE   # ns
NOISE_EQUALIZE = 5 #ADC
MAX_SIGNAL = 4095 #ADC
WINDOW_SIZE = 18.75*1e6 #MHz
n_of_windows = 3
SIMULATION_DURATION_NS= n_of_windows/(WINDOW_SIZE) *1e9 #ns
SIMULATION_DURATION_SAMPLES = int(SIMULATION_DURATION_NS / TIME_STEP)+1  # Number of samples in the simulation duration
print(TIME_STEP, SIMULATION_DURATION_NS, SIMULATION_DURATION_SAMPLES)


#preparring the sample pulse
with open('/home/shamshassiki/Shams_Analyzing_scripts/Trigger_simulation_and_tests/jsons/upsampled_2filter_pulse_example.json') as f:
    pulse_data = json.load(f)

pulse_voltage = np.array(pulse_data['avg_wave'])
pulse_time = np.array(pulse_data['t_axis_ns'])
pulse_start_time, pulse_end_time = 450, 570  # ns
pulse_voltage = pulse_voltage[(pulse_time >= pulse_start_time) & (pulse_time <= pulse_end_time)] / np.max(pulse_voltage)  # Normalized
pulse_time = pulse_time[(pulse_time >= pulse_start_time) & (pulse_time <= pulse_end_time)]
pulse_time = pulse_time - pulse_time[0]  # Start from 0 ns


#Noise makier
impulse_response_path   = Path("/home/shamshassiki/Shams_Analyzing_scripts/Trigger_simulation_and_tests/jsons/impulse_response_Freauency_35_240.json")


def make_band_limited_noise(json_path,
                            channel_key="ch0",
                            window_ns=1000.0,
                            adc_rate_ghz=0.472,   # hardware sampling rate
                            oversample=1,         # use >1 for fractional-ns step
                            target_rms_mV=1.0,
                            rng=None):
    """
    Return (time_ns, noise_mV) for one random noise realisation whose
    spectrum follows the magnitude in `json_path[channel_key]`.

    Parameters
    ----------
    json_path : str | Path
        Path to impulse-response JSON containing keys 'freq_GHz' + channels.
    channel_key : str
        Which channel’s magnitude to use as the band-pass shape.
    window_ns : float
        Length of the output trace in nanoseconds.
    adc_rate_ghz : float
        Native ADC rate of the system (GHz).
    oversample : int
        Upsampling factor applied before the FFT (Δt = 1/(adc_rate*oversample)).
    target_rms_mV : float
        RMS of the returned waveform, in millivolts.
    rng : numpy.random.Generator | None
        Source of randomness (defaults to np.random.default_rng()).

    Returns
    -------
    time_ns : 1-D ndarray
        Time axis in nanoseconds.
    noise_mV : 1-D ndarray
        Band-limited noise in millivolts, rms ≈ `target_rms_mV`.
    """
    # ---------- load magnitude response ------------
    data = json.loads(Path(json_path).read_text())
    freq_ref   = np.asarray(data["freq_GHz"])        # GHz
    mag_ref    = np.asarray(data[channel_key])

    # ---------- define FFT grid --------------------
    dt_ns  = 1.0 / (adc_rate_ghz * oversample)       # ns
    N      = int(round(window_ns / dt_ns))
    dt_s   = dt_ns * 1e-9
    freq_Hz = np.fft.rfftfreq(N, d=dt_s)
    freq_GHz = freq_Hz / 1e9

    # ---------- interpolate → Rayleigh σ -----------
    sigma = np.interp(freq_GHz, freq_ref, mag_ref, left=0.0, right=0.0)

    # ---------- draw random spectrum ---------------
    rng = rng or np.random.default_rng()
    amp   = rng.rayleigh(scale=sigma)
    phase = rng.uniform(0, 2*np.pi, size=amp.size)
    spec  = amp * np.exp(1j * phase)

    # ---------- IFFT to time domain ----------------
    noise = np.fft.irfft(spec, n=N)

    # ---------- normalise RMS ----------------------
    rms = np.sqrt(np.mean(noise ** 2)) or 1.0
    noise_mV = noise / rms * target_rms_mV

    time_ns = np.arange(N) * dt_ns
    return time_ns, noise_mV



def generate_pulse (pulse_v, pulse_t , STEP, simulation_index_duration, amplitude_scale):
    start_time= random.uniform(0, STEP)
    start_index= np.argmin(np.where(pulse_t >= start_time)[0])
    pulse_indices= np.linspace(start_index, len(pulse_v)-1, simulation_index_duration, dtype=int)
    

    if pulse_indices[-1] > len(pulse_v):
        raise ValueError("Pulse exceeds total duration when placed at the specified start time.")

    signal = pulse_v[pulse_indices] * amplitude_scale  # Scale the pulse voltage
    return signal

t, noise = make_band_limited_noise(json_path=impulse_response_path,
                                   channel_key="ch2_2x_amp",
                                   window_ns=SIMULATION_DURATION_NS,
                                   adc_rate_ghz=SAMPLING_RATE,
                                   target_rms_mV=NOISE_EQUALIZE)
pulse= generate_pulse(pulse_voltage, pulse_time, TIME_STEP, SIMULATION_DURATION_SAMPLES, amplitude_scale=40)    
signal= noise + pulse

plt.figure(figsize=(12, 6))
plt.plot(t, signal, label='Signal with Noise', color='blue')
plt.plot(t, pulse, label='Pulse', color='orange', alpha=0.7)
plt.plot(t, noise, label='Noise', color='green', alpha=0.5)
plt.title('Signal with Noise and Pulse')
plt.xlabel('Time (ns)')
plt.ylabel('Amplitude (mV)')
plt.legend()
plt.grid()
plt.savefig("signal_with_noise_and_pulse.png")