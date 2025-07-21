import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# -------------------- PARAMETERS --------------------
json_path = Path("nat.json")  # uploaded JSON file
output_png = Path("averaged_triggered_10_events.png")

START_EVENT = 50  # Starting event index (0 for the first event)
END_EVENT = 200  # Ending event index (exclusive, so this will include events

# ----------------------------------------------------

assert json_path.exists(), f"JSON file not found at {json_path}"

# -------------------- LOAD --------------------------
with json_path.open() as f:
    data = json.load(f)

events = data["events"]

# Detect channel names (assume keys that start with 'ch' followed by a digit)
example_event = events[0]
channel_names = sorted([k for k in example_event.keys() if k.startswith("ch")])

# -------------------- AVERAGE -----------------------
averaged = {}
for ch in channel_names:
    # Collect waveform arrays for this channel across all events
    waveforms = [np.array(evt[ch]) for evt in events]
    # Ensure common length (trim to the shortest)
    min_len = min(wf.size for wf in waveforms)
    stack = np.vstack([wf[:min_len] for wf in waveforms])
    averaged[ch] = stack.mean(axis=0)

# -------------------- PLOT --------------------------
plt.figure(figsize=(10, 6))
for ch in channel_names:
    plt.plot(averaged[ch][START_EVENT: END_EVENT], label=ch)

plt.title("Averaged Waveforms over 10 Triggered Events")
plt.xlabel("Sample #")
plt.ylabel("Amplitude (ADC)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

# Save to PNG
plt.savefig(output_png)
plt.close()

# -------------------- OUTPUT ------------------------
print(f"Averaged waveforms saved to {output_png}")
