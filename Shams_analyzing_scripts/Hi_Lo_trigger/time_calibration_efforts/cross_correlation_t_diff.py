
# NEW: SciPy for template fit
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import math   
import json, numpy as np, matplotlib.pyplot as plt
from pathlib import Path
import tools.waveform as waveform
import vpol_txrx as rxtx
from impulse_response import make_avg_wf

# ─────────────── USER-TUNABLE PARAMS ──────────────────────────────────────
UPSAMPLE_FACTOR = 100
SAMPLING_RATE   = 0.472            # GHz   (0.472 GS/s)
TIME_STEP       = 1.0 / SAMPLING_RATE   # ns

FREQ_MIN_GHZ    = 0.0               # ← adjust to zoom
FREQ_MAX_GHZ    = 1             # ← adjust to zoom

Cutoff_Freq_GHz = 0.00 # High-pass filter cutoff frequency, if needed

JSON_FILE       = Path("alignment_test_cross_corr_1.json")

# -------------------------------------------------------------------------
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


# ---------- 1. load JSON deep-chain data ----------------------------------

# Load JSON data
with open(JSON_FILE, 'r') as f:
    data = json.load(f)

plt.figure(figsize=(10, 5))
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
t_axis = np.arange(0, len_events) * TIME_STEP / UPSAMPLE_FACTOR  # Time axis in nano-seconds

def make_window(t_axis, center_ns, width_ns=200, edge_ns=20):
    """
    Returns a smooth window function centered at center_ns, with main width width_ns,
    and smooth edges of edge_ns using a raised cosine (Tukey-like) profile.
    """
    window = np.zeros_like(t_axis)
    start = center_ns - width_ns / 2
    stop = center_ns + width_ns / 2
    edge = edge_ns

    # Main flat region
    flat = (t_axis >= (start + edge)) & (t_axis <= (stop - edge))
    window[flat] = 1.0

    # Rising edge
    rise = (t_axis >= start) & (t_axis < start + edge)
    window[rise] = 0.5 * (1 - np.cos(np.pi * (t_axis[rise] - start) / edge))

    # Falling edge
    fall = (t_axis > stop - edge) & (t_axis <= stop)
    window[fall] = 0.5 * (1 + np.cos(np.pi * (t_axis[fall] - (stop - edge)) / edge))

    return window

# Example: center window at the max of channel 0
center_ns = t_axis[np.argmin(avg_waves[0].voltage)]
window = make_window(t_axis, center_ns, width_ns=280, edge_ns=40)
# Apply the window to each averaged waveform to restrict them
for ch in range(num_channels):
    avg_waves[ch].voltage = avg_waves[ch].voltage * window

def find_delays_correlation(waves, sample_rate_ghz,UPSAMPLE_FACTOR):
    """
    Args
    ----
    waves: list of 1-D numpy arrays, all same length, waves[0] is reference
    sample_rate_ghz: sampling rate in GHz (e.g. 0.472)

    Returns
    -------
    delays_ns: numpy array of per-channel delays (ns), latest channel = 0
    """
    ref = waves[0].voltage
    n = len(ref)
    delays_samples = []

    for wf in waves:
        # full x-correlation
        wf = wf.voltage
        corr = np.correlate(wf, ref, mode='full')
        # index of maximum correlation
        lag = np.argmax(corr) - (n - 1)          # samples
        delays_samples.append(lag)

    delays_samples = np.array(delays_samples, dtype=float)

    # convert to nanoseconds
    dt_per_sample = 1.0 / (sample_rate_ghz * 1e9) * 1e9/UPSAMPLE_FACTOR   # ns per sample
    delays_ns = delays_samples * dt_per_sample
    delays_ns = np.round(delays_ns, 3)  # round to 2 decimal places
    # shift so the latest channel reads 0
    delays_ns = delays_ns - delays_ns.max()

    return delays_ns


# ---- call it ---------------------------------------------------------
delays = find_delays_correlation(avg_waves, SAMPLING_RATE, UPSAMPLE_FACTOR)
print("Delays relative to latest channel (ns):", delays)

#saving example averaged pulse in JSON format
output_data = {
    "t_axis_ns": t_axis.tolist(),
    "avg_wave": avg_waves[0].voltage.tolist()
}
output_file = 'upsampled_2filter_pulse_example.json'
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=4)

#Plot the averaged waveforms with the window function
plt.figure(figsize=(12, 6))
for ch, wave in enumerate(avg_waves):
    #plt.plot(t_axis, wave.voltage, label=f'Ch{ch} raw', alpha=0.5)
    plt.plot(t_axis, wave.voltage * window, label=f'Ch{ch} windowed')

plt.plot(t_axis, window * np.max([np.max(np.abs(w.voltage)) for w in avg_waves]), 'k--', label='Window (scaled)')
plt.xlabel("Time (ns)")
plt.ylabel("Voltage (a.u.)")
plt.title("Averaged Waveforms and Window Function")
plt.legend(fontsize=8, loc='upper right')
plt.xlim(400, 600)  # Adjust x-axis limit as needed
plt.tight_layout()
plt.savefig('alignment_test_______________.png', dpi=300)



