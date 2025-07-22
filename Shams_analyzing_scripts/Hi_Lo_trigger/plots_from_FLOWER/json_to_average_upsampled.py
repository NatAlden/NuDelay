import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import resample   # FFT-based

# ──────────────────────────────── CLI ────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--json", default="nat.json",
                    help="path to the input JSON file")
parser.add_argument("--out",  default="averaged_triggered_10_events.png",
                    help="output PNG path")
parser.add_argument("--upsampling_factor", type=int, default=1,
                    help="integer factor (≥1) for FFT up-sampling")
args = parser.parse_args()

ups = 10
channels = ["ch0", "ch1", "ch2", "ch3"]      # hard-coded order

START_EVENT = 500  # Starting event index (0 for the first event)
END_EVENT = 1800  # Ending event index (exclusive, so this will include events
output_png = Path("averaged_triggered_10_upsampled.png")

# ──────────────────────────── load & collect ─────────────────────────
with Path(args.json).open() as f:
    data = json.load(f)["events"]            # top-level key is “events”

# channel_data[ch] → list of np arrays (one per event)
channel_data = {ch: [] for ch in channels}

for ev in data:
    for ch in channels:
        raw = np.asarray(ev[ch], dtype=float)          # 1-D vector
        if ups > 1:                                    # optional FFT resample
            new_N = len(raw) * ups
            raw = resample(raw, new_N, axis=0)
        channel_data[ch].append(raw)

# ───────────────────────────── averaging ─────────────────────────────
avg = {ch: np.mean(np.vstack(channel_data[ch]), axis=0)
       for ch in channels}

# make a common x-axis (samples)
x = np.arange(avg["ch0"].size)

# ─────────────────────────────── plot ────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
for ch in channels:
    ax.plot(x[START_EVENT: END_EVENT], avg[ch][START_EVENT: END_EVENT], label=ch)

ax.set_xlabel("sample index")
ax.set_ylabel("ADC counts")
ax.set_title(f"Averaged waveforms (upsampling ×{ups})")
ax.legend()
ax.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(output_png, dpi=150)
