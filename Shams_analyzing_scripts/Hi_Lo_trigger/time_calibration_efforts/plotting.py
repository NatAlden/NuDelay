
import json, numpy as np, matplotlib.pyplot as plt
from pathlib import Path
import tools.waveform as waveform
import vpol_txrx as rxtx
from impulse_response import make_avg_wf



# ─────────────── USER-TUNABLE PARAMS ──────────────────────────────────────
UPSAMPLE_FACTOR = 1
SAMPLING_RATE   = 0.472            # GHz   (0.472 GS/s)
TIME_STEP       = 1.0 / SAMPLING_RATE   # ns

FREQ_MIN_GHZ    = 0.0               # ← adjust to zoom
FREQ_MAX_GHZ    = 1             # ← adjust to zoom

Cutoff_Freq_GHz = 0.00 # High-pass filter cutoff frequency, if needed
event_idx = 90  # Change this index to select a different event
xlim_1, xlim_2 = 210, 290  # X-axis limits for the plot

JSON_FILE       = Path("time_delay_test_20deg_18.json")
# ---------- 1. load JSON deep-chain data ----------------------------------

# Load JSON data
with open(JSON_FILE, 'r') as f:
    data = json.load(f)

plt.figure(figsize=(10, 5))
data = data["events"]  # Extract events from the JSON data
num_channels = 4  # Number of channels in the JSON file
num_events = len(data)  # Number of events to process, adjust as needed
print(f'Number of events: {num_events}')

# Choose which event to plot (0 <= event_idx < num_events)


# Collect waveforms for the selected event
event = data[event_idx]
channel_waves = []
for ch in range(num_channels):
    key = f'ch{ch}'
    wf = waveform.Waveform(np.array(event[key]))
    channel_waves.append(wf)

len_samples = len(channel_waves[0].voltage)
t_axis = np.arange(0, len_samples) * TIME_STEP  # Time axis in nano-seconds

# Plot the waveforms for the selected event
plt.figure(figsize=(12, 6))
for ch, wave in enumerate(channel_waves):
    plt.plot(t_axis, wave.voltage, label=f'Ch{ch}')

plt.xlabel("Time (ns)")
plt.ylabel("Voltage (a.u.)")
plt.xlim(xlim_1, xlim_2)  # Set x-axis limits
plt.title(f"Waveforms for Event {event_idx}")
plt.legend(fontsize=8, loc='upper right')
plt.tight_layout()
plt.savefig(f'waveforms_event_{event_idx}.png', dpi=300)



