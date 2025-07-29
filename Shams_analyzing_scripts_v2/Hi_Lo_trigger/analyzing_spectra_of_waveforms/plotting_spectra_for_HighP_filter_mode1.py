
import json, numpy as np, matplotlib.pyplot as plt
from pathlib import Path
import tools.waveform as waveform
import vpol_txrx as rxtx
from impulse_response import make_avg_wf



# ─────────────── USER-TUNABLE PARAMS ──────────────────────────────────────
UPSAMPLE_FACTOR = 10
SAMPLING_RATE   = 0.472            # GHz   (0.472 GS/s)
TIME_STEP       = 1.0 / SAMPLING_RATE   # ns

FREQ_MIN_GHZ    = 0.0               # ← adjust to zoom
FREQ_MAX_GHZ    = 1             # ← adjust to zoom

Cutoff_Freq_GHz = 0.0  # High-pass filter cutoff frequency, if needed

JSON_FILE       = Path("atten_50_with_HighPass_trig_mode_1.json")
CSV_FILE        = Path("cal_output_31atten_Ch2.csv")
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
center_ns = t_axis[np.argmax(avg_waves[0].voltage)]
window = make_window(t_axis, center_ns, width_ns=280, edge_ns=40)

# Apply the window to each averaged waveform to restrict them
for ch in range(num_channels):
    avg_waves[ch].voltage = avg_waves[ch].voltage * window

""" Plot the averaged waveforms with the window function
plt.figure(figsize=(12, 6))
for ch, wave in enumerate(avg_waves):
    #plt.plot(t_axis, wave.voltage, label=f'Ch{ch} raw', alpha=0.5)
    plt.plot(t_axis, wave.voltage * window, label=f'Ch{ch} windowed')

plt.plot(t_axis, window * np.max([np.max(np.abs(w.voltage)) for w in avg_waves]), 'k--', label='Window (scaled)')
plt.xlabel("Time (ns)")
plt.ylabel("Voltage (a.u.)")
plt.title("Averaged Waveforms and Window Function")
plt.legend(fontsize=8, loc='upper right')
plt.tight_layout()
plt.savefig('averaged_waveforms_with_window.png', dpi=300)
"""


# ---------- 2. FFT of each averaged channel ------------------------------
plt.figure(figsize=(12, 6))
for ch, wave in enumerate(avg_waves):
    voltage = wave.voltage
    N = len(voltage)
    # Calculate actual time step from t_axis
    if len(t_axis) > 1:
        dt = t_axis[1] - t_axis[0]  # Time step in ns
    else:
        dt = TIME_STEP
    # Frequency axis in GHz (since TIME_STEP is in ns, 1/ns = GHz)
    xf = np.fft.fftfreq(N, d=dt)[:N // 2]
    yf = np.abs(np.fft.fft(voltage))[:N // 2]

    mask = (xf >= Cutoff_Freq_GHz)

    xf = xf[mask]
    yf = yf[mask]
    plt.plot(xf, yf / np.max(yf), label=f'Channel {ch}')

# ---------- 3. load cal-pulser CSV & FFT ---------------------------------
raw = np.genfromtxt(CSV_FILE, delimiter=",", usecols=(3, 4), dtype=float,
                    invalid_raise=False)
raw = raw[~np.isnan(raw).any(axis=1)]
time_s, amp = raw[:, 0], raw[:, 1]

dt_cal   = np.median(np.diff(time_s))
freq_cal = np.fft.rfftfreq(len(amp), d=dt_cal) / 1e9  # GHz
mag_cal  = np.abs(np.fft.rfft(amp))
mask_cal = (freq_cal >= Cutoff_Freq_GHz)
freq_cal = freq_cal[mask_cal]
mag_cal  = mag_cal[mask_cal]

# ---------- 4. single composite plot -------------------------------------


plt.plot(freq_cal, mag_cal / np.max(mag_cal), lw=1.5, color="k", label="cal-pulser (normalized)")

plt.xlabel("frequency (GHz)")
plt.ylabel("amplitude (a.u.)")
plt.title("Deep-chain averaged channels + cal-pulser  •  frequency domain (with high-pass filter)")
plt.xlim(FREQ_MIN_GHZ, FREQ_MAX_GHZ)
plt.ylim(0, 1.2 )  # Adjust y-limits to fit all curves
plt.grid(True, lw=0.3, alpha=0.7)
plt.legend(ncol=3, fontsize=8)
plt.tight_layout()
plt.savefig("combined_frequency_domain_windowed_HighP_filter_mode1_no_mask.png", dpi=300)
plt.show()
