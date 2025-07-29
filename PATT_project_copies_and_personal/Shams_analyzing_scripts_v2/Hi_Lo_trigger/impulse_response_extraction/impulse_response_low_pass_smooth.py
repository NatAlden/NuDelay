#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep-chain impulse responses, mean-subtracted and smooth-low-pass (240 MHz).
Outputs:
  • low_pass240_frequency_domain.png
  • deep_impulse_responses_lowpass240.json
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import tools.waveform as waveform
import vpol_txrx as rxtx

# ─── Constants ──────────────────────────────────────────────────────────────
RADIANT_SAMPLING_RATE = 2.400        # ns per sample
UPSAMPLE_FACTOR       = 40

F_CUT          = 0.240               # GHz  (-3 dB corner)
TRANSITION_BW  = 0.020               # GHz  (halfwidth of raised-cosine roll-off)

# ─── Deep-only file list ────────────────────────────────────────────────────
directory = "/mnt/labdata/chicago-rnog-system-response-2024/lab_measurements/labdata/"
deep_files = [
    "fullchain_deep_channel2_lowthreshon_fastimpulse.json",
    "fullchain_deep_channel2_lowthreshon_fastimpulse+6dB.json",
    "fullchain_deep_channel9_lowthreshon_fastimpulse+6dB.json",
    "fullchain_deep_channel11_lowthreshon_fastimpulse+6dB.json"
]

labels = ["ch2 × 2 amp", "ch2", "ch9", "ch10"]   # keys for JSON / legend

# ─── Helper functions ───────────────────────────────────────────────────────
def make_avg_wf(waves, upsamp=UPSAMPLE_FACTOR):
    """Align (max-corr), up-sample in frequency, and average."""
    avg = waves[0]
    avg.fft(); avg.upsampleFreqDomain(upsamp)
    for w in waves[1:]:
        w.fft(); w.upsampleFreqDomain(upsamp)
        delay = int(np.argmax(w.crossCorrelate(avg)) - len(w.voltage)/2)
        w.voltage = np.roll(w.voltage, -delay)
        avg.voltage += w.voltage
    avg.voltage /= len(waves)
    return avg

def load_radiant_wfs(path, thr=180):
    """Return Waveform objects whose |V| peaks exceed threshold (mean-subtracted)."""
    with open(path) as f:
        data = json.load(f)
    keep = []
    for ev in data:
        raw = np.array(ev["radiant_waveforms"], dtype=float)
        raw -= raw.mean()                                # ← mean subtraction
        idx = np.argmax(np.abs(raw))
        if max(np.abs(raw)) > thr and 40 < idx < 2000:
            keep.append(waveform.Waveform(raw,
                                          sampling_rate=1./RADIANT_SAMPLING_RATE))
    return keep

def smooth_lowpass_filter(wf, f_cut=F_CUT, trans_bw=TRANSITION_BW):
    """Raised-cosine low-pass filter applied in frequency domain."""
    wf.fft()
    f     = wf.freq                                    # GHz
    gain  = np.ones_like(f)
    f1, f2 = f_cut - trans_bw, f_cut + trans_bw
    gain[f >= f2] = 0.0                                # stop-band
    transition = (f > f1) & (f < f2)
    gain[transition] = 0.5 * (1 + np.cos(np.pi * (f[transition] - f1)/(f2 - f1)))
    wf.ampl *= gain
    wf.voltage = np.fft.irfft(wf.ampl, n=len(wf.voltage))
    return wf

# ─── Main processing loop ───────────────────────────────────────────────────
avg_resp = []
for fname in deep_files:
    waves = load_radiant_wfs(directory + fname, thr=180)
    avg   = make_avg_wf(waves)
    avg.voltage = np.roll(avg.voltage,
                          -int(np.argmax(avg.voltage) - len(avg.voltage)/2))
    avg.medianSubtract()
    avg.voltage = rxtx.window(avg.voltage, 20000)
    avg.voltage[:np.where(avg.time > 415)[0][0]] = 0.0
    avg = smooth_lowpass_filter(avg)
    avg_resp.append(avg)

# ─── Frequency-domain quick-look plot ───────────────────────────────────────
plt.figure(figsize=(8,4))
for wf, lab in zip(avg_resp, labels):
    plt.plot(wf.freq,
             np.abs(wf.ampl)/np.max(np.abs(wf.ampl)),
             label=lab, lw=1)
plt.xlabel("Frequency (GHz)")
plt.ylabel("Normalised amplitude")
plt.title("Deep-chain spectra (smooth LP @ 240 MHz, mean-subtracted)")
plt.xlim(0, 0.5)
plt.grid(True, lw=0.3)
plt.legend(ncol=2, fontsize=8)
plt.tight_layout()
plt.savefig("low_pass240_frequency_domain.png", dpi=200)

# ─── Save JSON ──────────────────────────────────────────────────────────────
deep_ir = {"time": avg_resp[0].time.tolist()}
for wf, lab in zip(avg_resp, labels):
    deep_ir[lab.replace(" ", "")] = (wf.voltage / np.max(np.abs(wf.voltage))).tolist()

with open("deep_impulse_responses_lowpass240.json", "w") as f:
    json.dump(deep_ir, f, indent=2)
