import json
import numpy as np
import tools.waveform as waveform
import vpol_txrx as rxtx

# Constants
RADIANT_SAMPLING_RATE = 2.400
UPSAMPLE_FACTOR = 40
f_low = 0.000  # GHz
f_high = 0.240  # GHz

# File list
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

# Load and preprocess
def make_avg_wf(wave_list, upsamp=UPSAMPLE_FACTOR):
    avg = wave_list[0]
    avg.fft()
    avg.upsampleFreqDomain(upsamp)
    for wave in wave_list[1:]:
        wave.fft()
        wave.upsampleFreqDomain(upsamp)
        delay = int(np.argmax(wave.crossCorrelate(avg)) - len(wave.voltage) / 2)
        wave.voltage = np.roll(wave.voltage, -delay)
        avg.voltage += wave.voltage
    avg.voltage /= float(len(wave_list))
    return avg

def load_and_list_radiant_wfs(filepath, threshold=180):
    with open(filepath, "r") as f:
        data = json.load(f)
    wfs = []
    for ev in data:
        wf = ev["radiant_waveforms"]
        if max(np.abs(wf)) > threshold and 40 < np.argmax(np.abs(wf)) < 2000:
            wfs.append(waveform.Waveform(wf, sampling_rate=1./RADIANT_SAMPLING_RATE))
    return wfs

def bandpass_filter(wf, f_low, f_high):
    wf.fft()
    mask = (wf.freq >= f_low) & (wf.freq <= f_high)
    wf.ampl[~mask] = 0
    wf.voltage = np.fft.irfft(wf.ampl, n=len(wf.voltage))
    return wf

# Main processing
avg_impulse_response = []

for fname in filenames:
    threshold = 50 if fname == "deep_channel10.json" else 180
    wfs = load_and_list_radiant_wfs(directory + fname, threshold=threshold)
    avg = make_avg_wf(wfs)
    avg.voltage = np.roll(avg.voltage, -int(np.argmax(avg.voltage) - len(avg.voltage) / 2))
    avg.medianSubtract()
    avg.voltage = rxtx.window(avg.voltage, 20000)
    avg.voltage[:np.where(avg.time > 415)[0][0]] = 0.0
    avg = bandpass_filter(avg, f_low, f_high)
    avg_impulse_response.append(avg)

# Save deep response
deep_ir = {
    'time': avg_impulse_response[0].time.tolist(),
    'ch2_2x_amp': (avg_impulse_response[0].voltage / np.max(avg_impulse_response[0].voltage)).tolist(),
    'ch2': (avg_impulse_response[1].voltage / np.max(avg_impulse_response[1].voltage)).tolist(),
    'ch9': (avg_impulse_response[2].voltage / np.max(avg_impulse_response[2].voltage)).tolist(),
    'ch10': (avg_impulse_response[3].voltage / np.max(avg_impulse_response[3].voltage)).tolist()
}
with open('deep_impulse_responses_low_pass.json', 'w') as f:
    json.dump(deep_ir, f)

# Save surface response
surf_ir = {
    'time': avg_impulse_response[4].time.tolist(),
    'ch13_2x_amp': (avg_impulse_response[4].voltage / np.max(avg_impulse_response[4].voltage)).tolist(),
    'ch13': (avg_impulse_response[5].voltage / np.max(avg_impulse_response[5].voltage)).tolist(),
    'ch14_2x_amp': (avg_impulse_response[6].voltage / np.max(avg_impulse_response[6].voltage)).tolist(),
    'ch14': (avg_impulse_response[7].voltage / np.max(avg_impulse_response[7].voltage)).tolist()
}
with open('surface_impulse_responses.json', 'w') as f:
    json.dump(surf_ir, f)

