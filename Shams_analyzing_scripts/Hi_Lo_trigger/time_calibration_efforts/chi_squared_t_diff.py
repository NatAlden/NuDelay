
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

JSON_FILE       = Path("alignment_test_chi2_set0_4.json")

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


def _best_shift_by_chi2(ref, tgt, coarse_shift, search=50):
    """
    Scan shifts in [coarse_shift - search , coarse_shift + search] samples.
    For each shift, fit tgt to A*ref + B (least-squares) and keep the
    shift with the minimum chi-squared.  Returns (best_shift_samples, chi2).
    """
    best_chi2  = math.inf
    best_shift = coarse_shift

    x = ref
    mx = x.mean()
    var_x = ((x - mx) ** 2).mean()

    for s in range(coarse_shift - search, coarse_shift + search + 1):
        y = np.roll(tgt, -s)
        my = y.mean()
        cov_xy = ((x - mx) * (y - my)).mean()

        A = cov_xy / var_x if var_x != 0 else 0.0
        B = my - A * mx
        resid = y - (A * x + B)
        chi2  = np.square(resid).sum()

        if chi2 < best_chi2:
            best_chi2, best_shift = chi2, s

    return best_shift, best_chi2

def print_delays_chi2_refined(avg_waves, t_axis, search_samples=50):
    """
    Reference = channel whose peak arrives last.
    Delay for every other channel = how many ns it leads that reference,
    refined with a ±search_samples chi-squared scan around the argmax shift.
    """
    dt_ns = t_axis[1] - t_axis[0]                # ns per up-sampled bin

    # Identify reference channel (latest peak)
    peak_idx  = [np.argmax(w.voltage) for w in avg_waves]
    ref_ch    = int(np.argmax(peak_idx))
    ref_wave  = avg_waves[ref_ch].voltage
    ref_peak  = peak_idx[ref_ch]

    delays_ns = [0.0] * len(avg_waves)           # fill with zeros first

    for ch, w in enumerate(avg_waves):
        if ch == ref_ch:
            continue

        coarse = peak_idx[ch] - ref_peak
        best_shift, _ = _best_shift_by_chi2(
            ref_wave, w.voltage, coarse_shift=coarse, search=search_samples
        )
        # Positive delay = channel arrives earlier than reference
        delays_ns[ch] = -best_shift * dt_ns

    # Print nicely
    print(f"\nReference (latest peak) channel: Ch{ref_ch}")
    print("Delays ahead of reference (chi-squared refined):")
    for ch, d in enumerate(delays_ns):
        print(f"  Ch{ch}: {d:+7.3f} ns")

# ---- call it ---------------------------------------------------------
print_delays_chi2_refined(avg_waves, t_axis, search_samples=50)


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
plt.savefig('alignment_test_0delays.png', dpi=300)



