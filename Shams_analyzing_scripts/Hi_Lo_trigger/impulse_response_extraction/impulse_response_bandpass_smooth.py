#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep-chain impulse responses with smooth 70-240 MHz band-pass filtering.
Outputs:
  • bandpass70-240_frequency_domain.png
  • deep_impulse_responses_bandpass70-240.json
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import tools.waveform as waveform
import vpol_txrx as rxtx

# ─── Constants ──────────────────────────────────────────────────────────────
RADIANT_SAMPLING_RATE = 2.400        # ns per sample
UPSAMPLE_FACTOR       = 40

F_LO          = 0.035               # GHz  (band starts   @ −3 dB)
F_HI          = 0.240               # GHz  (band ends     @ −3 dB)
TRANSITION_BW = 0.020               # GHz  (half of raised-cosine roll-off width)

# ─── Deep-only file list ────────────────────────────────────────────────────
directory = "/mnt/labdata/chicago-rnog-system-response-2024/lab_measurements/labdata/"
deep_files = [
    "fullchain_deep_channel2_lowthreshon_fastimpulse.json",
    "fullchain_deep_channel2_lowthreshon_fastimpulse+6dB.json",
    "fullchain_deep_channel9_lowthreshon_fastimpulse+6dB.json",
    "fullchain_deep_channel11_lowthreshon_fastimpulse+6dB.json"
]
labels = ["ch2x2", "ch2", "ch9", "ch10"]          # keys / legend text

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
    """Yield Waveform objects (>thr) with mean subtracted."""
    with open(path) as f:
        data = json.load(f)
    keep = []
    for ev in data:
        raw = np.asarray(ev["radiant_waveforms"], float)
        raw -= raw.mean()                                   # mean-centre
        idx = np.argmax(np.abs(raw))
        if max(np.abs(raw)) > thr and 40 < idx < 2000:
            keep.append(waveform.Waveform(raw,
                                          sampling_rate=1./RADIANT_SAMPLING_RATE))
    return keep

def smooth_bandpass_filter(wf, f_lo=F_LO, f_hi=F_HI, bw=TRANSITION_BW):
    """
    Raised-cosine band-pass:
        - - pass-band  : f_lo+bw  ≤ f ≤ f_hi-bw  →  gain = 1
        - - stop-band  : f ≤ f_lo-bw  or  f ≥ f_hi+bw  →  gain = 0
        - - raised-cos roll-offs in the two transition regions.
    """
    wf.fft()
    f = wf.freq                                          # GHz
    gain = np.zeros_like(f)

    # upper & lower transition edges
    lo1, lo2 = f_lo - bw, f_lo + bw
    hi1, hi2 = f_hi - bw, f_hi + bw

    # pass-band
    gain[(f >= lo2) & (f <= hi1)] = 1.0

    # low-edge roll-on
    lo_mask = (f > lo1) & (f < lo2)
    gain[lo_mask] = 0.5 * (1 - np.cos(np.pi * (f[lo_mask] - lo1) / (2*bw)))

    # high-edge roll-off
    hi_mask = (f > hi1) & (f < hi2)
    gain[hi_mask] = 0.5 * (1 + np.cos(np.pi * (f[hi_mask] - hi1) / (2*bw)))

    wf.ampl *= gain
    wf.voltage = np.fft.irfft(wf.ampl, n=len(wf.voltage))
    return wf

# ─── Main processing loop ───────────────────────────────────────────────────
avg_resp = []
for fname in deep_files:
    waves = load_radiant_wfs(directory + fname, thr=180)
    avg   = make_avg_wf(waves)

    # centre, median-subtract, window, remove pre-trigger
    avg.voltage = np.roll(avg.voltage,
                          -int(np.argmax(avg.voltage) - len(avg.voltage)/2))
    avg.medianSubtract()
    avg.voltage = rxtx.window(avg.voltage, 20000)
    avg.voltage[:np.where(avg.time > 415)[0][0]] = 0.0

    # apply smooth band-pass
    avg = smooth_bandpass_filter(avg)
    avg_resp.append(avg)

# ─── Frequency-domain quick-look plot ───────────────────────────────────────
plt.figure(figsize=(8,4))
for wf, lab in zip(avg_resp, labels):
    plt.plot(wf.freq,
             np.abs(wf.ampl)/np.max(np.abs(wf.ampl)),
             label=lab, lw=1)
plt.xlabel("Frequency (GHz)")
plt.ylabel("Normalised amplitude")
plt.title("Deep-chain spectra (smooth 35–240 MHz band-pass, mean-subtracted)")
plt.xlim(0, 0.5)
plt.grid(True, lw=0.3)
plt.legend(ncol=2, fontsize=8)
plt.tight_layout()
plt.savefig("bandpass35-240_frequency_domain.png", dpi=200)

# ─── Save JSON ──────────────────────────────────────────────────────────────
deep_ir = {"time": avg_resp[0].time.tolist()}
for wf, lab in zip(avg_resp, labels):
    deep_ir[lab] = (wf.voltage / np.max(np.abs(wf.voltage))).tolist()

with open("deep_impulse_responses_bandpass35-240.json", "w") as f:
    json.dump(deep_ir, f, indent=2)
