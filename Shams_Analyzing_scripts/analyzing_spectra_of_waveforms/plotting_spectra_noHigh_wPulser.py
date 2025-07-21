
import json
import numpy as np
import sys
import os
import vpol_txrx as rxtx
import matplotlib.pyplot as plt
import tools.waveform as waveform
import tools.myplot
import scipy
from pathlib import Path

JSON_FILE = 'atten_50_no_HighPass_trig_mode_0.json'
CSV_FILE = 'cal_output_31atten_Ch2.csv'


# Constants
UPSAMPLE_FACTOR = 10
SAMPLING_RATE = 0.472  # GHz
TIME_STEP = 1.0 / SAMPLING_RATE  # Time step in nano-seconds





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


# Load JSON data
with open(JSON_FILE, 'r') as f:
    data = json.load(f)


data = data["events"]  # Extract events from the JSON data
num_channels = 4  # Number of channels in the JSON file
num_events = len(data)  # Number of events to process, adjust as needed
print(f'Number of events: {num_events}')

# Collect waveforms for each channel
channel_waves = [[] for _ in range(num_channels)]

for event in data[3:]:
    for ch in range(num_channels):
        # Adjust key if needed, e.g., 'channel_0', 'ch0', etc.
        key = f'ch{ch}'
        # Convert list of voltages to waveform object
        wf = waveform.Waveform(np.array(event[key]))
        channel_waves[ch].append(wf)

# Compute average, upsampled waveforms for each channel
avg_waves = []
for ch in range(num_channels):
    avg_wave = make_avg_wf(channel_waves[ch], upsamp=UPSAMPLE_FACTOR, method='cor')
    avg_waves.append(avg_wave)

len_events = len(avg_waves[0].voltage)  # Length of the averaged waveform
t_axis = np.arange(0, len_events) * (TIME_STEP/UPSAMPLE_FACTOR)  # Time axis in nano-seconds
print(f'Length of averaged waveform: {len_events} samples ({len_events * TIME_STEP/UPSAMPLE_FACTOR:.2f} ns)')

plt.figure(figsize=(12, 6))
for ch, wave in enumerate(avg_waves):
    plt.plot(t_axis, wave.voltage, label=f'Channel {ch}')

plt.title('Averaged, Upsampled Waveforms (Time Domain)')
plt.xlabel('Time (ns)')
plt.ylabel('Amplitude')
plt.xlim(100, 350)  # Adjust x-axis limit
plt.legend()
plt.tight_layout()
plt.savefig('averaged_waveforms_time_domain.png', dpi=300)
plt.show()
plt.savefig('averaged_waveforms_time_domain.png', dpi=300)
plt.show()
plt.clf()



plt.figure(figsize=(12, 6))
for ch, wave in enumerate(avg_waves):
    voltage = wave.voltage
    N = len(voltage)
    dt = TIME_STEP  # Time step in ns
    # Frequency axis in GHz (since TIME_STEP is in ns, 1/ns = GHz)
    xf = np.fft.fftfreq(N, d=dt)[:N // 2]
    yf = np.abs(np.fft.fft(voltage))[:N // 2]
    plt.plot(xf, yf, label=f'Channel {ch}')

plt.title('Averaged, Upsampled Waveforms (Frequency Domain)')
plt.xlabel('Frequency (GHz)')
plt.ylabel('Amplitude')
plt.legend()
plt.tight_layout()
plt.savefig('averaged_waveforms_frequency_domain.png', dpi=300)
plt.show()




csv_path = Path("cal_output_31atten_Ch2.csv")  # adjust if needed

# ---------- load CSV (NumPy-only, no pandas) ------------------------------
# Use columns 3 (time [s]) and 4 (amplitude)
raw = np.genfromtxt(csv_path,
                    delimiter=",",
                    usecols=(3, 4),
                    dtype=float,
                    invalid_raise=False)          # non-numeric cells → nan

# drop rows that contained non-numeric entries
raw = raw[~np.isnan(raw).any(axis=1)]

time_s = raw[:, 0]
amp    = raw[:, 1]

# ---------- FFT -----------------------------------------------------------
dt      = np.median(np.diff(time_s))         # sample interval  [s]
freq_Hz = np.fft.rfftfreq(len(amp), d=dt)
spec    = np.fft.rfft(amp)
mag     = np.abs(spec)

freq_GHz = freq_Hz / 1e9

# ---------- plot ----------------------------------------------------------
plt.figure(figsize=(9, 4))
plt.plot(freq_GHz, mag, lw=1.2)
plt.xlabel("frequency (GHz)")
plt.ylabel("amplitude (a.u.)")
plt.title("Cal pulser event • frequency domain")
plt.xlim(0, 2.5)  # Adjust as needed
plt.grid(True, lw=0.3, alpha=0.7)
plt.tight_layout()
plt.savefig("cal_pulser_event_frequency_domain.png", dpi=300)
plt.show()