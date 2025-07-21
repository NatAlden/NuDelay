#!/usr/bin/env python3
import argparse, json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import resample          # FFT-based up-sampling

# ─────────────────────────────── CLI ───────────────────────────────
p = argparse.ArgumentParser()
p.add_argument("--json", default="nat.json",  help="input JSON file")
p.add_argument("--out",
               default="averaged_triggered_10_upsampled.png",
               help="output PNG file")
p.add_argument("--upsampling_factor", type=int, default=10,
               help="integer ≥1, applied to *every* event before averaging")
args = p.parse_args()

ups          = 10
channels     = ["ch0", "ch1", "ch2", "ch3"]
START_EVENT  = 500                 # plotting window only
END_EVENT    = 1800
output_png= "averaged_triggered_10_shifted.png"

# ───────────────────────────── load JSON ───────────────────────────
with Path(args.json).open() as f:
    events = json.load(f)["events"]

# channel_data[ch] → list of *aligned & upsampled* numpy arrays
channel_data = {ch: [] for ch in channels}

# -------------------------------------------------------------------
# 1.  UPSAMPLE each raw waveform (FFT / sinc interpolation)
# 2.  DETECT its main peak (|adc| max)
# 3.  SHIFT so that all peaks line up with the reference index
# -------------------------------------------------------------------
def shift_to_index(arr, shift, fill=0.0):
    """Return a *new* array shifted by `shift` samples (int).
       Missing samples are filled with `fill` (no wrap-around)."""
    out = np.full_like(arr, fill)
    if shift >= 0:
        out[shift:] = arr[:-shift or None]
    else:
        out[:shift] = arr[-shift:]
    return out

for ch in channels:
    # --- First pass to measure peak locations (after up-sampling) ----
    peak_indices = []
    upsampled_ev = []       # cache to avoid recomputing
    for ev in events:
        raw  = np.asarray(ev[ch], dtype=float)
        up   = resample(raw, len(raw) * ups) if ups > 1 else raw
        upsampled_ev.append(up)
        peak_indices.append(np.argmax(np.abs(up)))      # |adc| peak

    # Choose a *reference* alignment index (median is robust)
    ref_idx = int(np.median(peak_indices))

    # --- Second pass: shift every event so its peak sits at ref_idx ---
    for up, pk in zip(upsampled_ev, peak_indices):
        shift = ref_idx - pk
        channel_data[ch].append(shift_to_index(up, shift, fill=0.0))

# ───────────────────────────── averaging ───────────────────────────
avg = {ch: np.mean(np.vstack(channel_data[ch]), axis=0) for ch in channels}
x   = np.arange(avg["ch0"].size)

# ────────────────────────────── plotting ───────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
for ch in channels:
    ax.plot(x[START_EVENT:END_EVENT],
            avg[ch][START_EVENT:END_EVENT],
            label=ch)

ax.set_xlabel("sample index")
ax.set_ylabel("ADC counts")
ax.set_title(f"Averaged, peak-aligned waveforms (upsampling ×{ups})")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(output_png, dpi=150)

