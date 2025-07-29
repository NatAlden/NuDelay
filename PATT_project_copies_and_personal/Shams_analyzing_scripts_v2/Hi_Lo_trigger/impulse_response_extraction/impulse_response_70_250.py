import json
import numpy as np
import matplotlib.pyplot as plt
import tools.waveform as waveform
import vpol_txrx as rxtx

# Constants
RADIANT_SAMPLING_RATE = 2.400
UPSAMPLE_FACTOR = 40

# File setup
directory = "/mnt/labdata/chicago-rnog-system-response-2024/lab_measurements/labdata/"
filenames = [
    "fullchain_deep_channel2_lowthreshon_fastimpulse.json",
    "fullchain_deep_channel2_lowthreshon_fastimpulse+6dB.json",
    "fullchain_deep_channel9_lowthreshon_fastimpulse+6dB.json",
    "fullchain_deep_channel11_lowthreshon_fastimpulse+6dB.json",
    "amps40dB_surface_channel_13.json",
    "amps46dB_surface_channel13.json",
    "amps40dB_surface_channel14.json",
    "amps46dB_surface_channel14.json",
    "deep_channel10.json"
]

# Frequency range to isolate [GHz]
f_low = 0.07
f_high = 0.25

# Functions
def make_avg_wf(wave_list, upsamp=UPSAMPLE_FACTOR):
    average_wf = wave_list[0]
    average_wf.fft()
    average_wf.upsampleFreqDomain(upsamp)
    for wave in wave_list[1:]:
        wave.fft()
        wave.upsampleFreqDomain(upsamp)
        cor = wave.crossCorrelate(average_wf)
        delay = int(np.argmax((cor)) - np.size(cor) / 2.)
        wave.voltage = np.roll(wave.voltage, -delay)
        average_wf.voltage += wave.voltage
    average_wf.voltage /= float(len(wave_list))
    return average_wf

def load_and_list_radiant_wfs(filename, threshold=180):
    with open(filename, "r") as run:
        data = json.load(run)
    wfs = []
    for ev in data:
        wf = ev["radiant_waveforms"]
        if max(np.abs(wf)) > threshold and 40 < np.argmax(np.abs(wf)) < 2000:
            wfs.append(waveform.Waveform(wf, sampling_rate=1./RADIANT_SAMPLING_RATE))
    return wfs

# Processing
avg_responses = []
for fname in filenames:
    full_path = directory + fname
    threshold = 50 if fname == "deep_channel10.json" else 180
    wfs = load_and_list_radiant_wfs(full_path, threshold=threshold)
    avg = make_avg_wf(wfs)
    avg.voltage = np.roll(avg.voltage, -int(np.argmax(avg.voltage) - len(avg.voltage) / 2))
    avg.medianSubtract()
    avg.voltage = rxtx.window(avg.voltage, 20000)
    avg.voltage[:np.where(avg.time > 415)[0][0]] = 0.0
    avg.fft()
    avg_responses.append(avg)

# Plotting frequency-domain response
plt.figure(figsize=(10, 5))
for i, avg in enumerate(avg_responses):
    mask = (avg.freq >= f_low) & (avg.freq <= f_high)
    freqs = avg.freq[mask]
    ampl = np.abs(avg.ampl[mask])
    ampl /= np.max(ampl) if np.max(ampl) != 0 else 1  # avoid divide by zero
    plt.plot(freqs, ampl, label=f'File {i}')

plt.xlabel("Frequency (GHz)")
plt.ylabel("Normalized Amplitude")
plt.title("Frequency-Domain Response")
plt.grid(True)
plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig("frequency_domain_response.png")

