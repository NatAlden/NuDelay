#!/usr/bin/env python3
"""
Deep-chain impulse responses with a raised-cosine band-pass:
35 MHz (turn-on) → 240 MHz (turn-off), 20 MHz transition each edge.
Outputs:
    • deep_impulse_responses_bandpass35-240.json
"""

import json
import numpy as np
import tools.waveform as waveform
import vpol_txrx as rxtx

# ─── constants ──────────────────────────────────────────────────────────────
RADIANT_SAMPLING_RATE = 2.400     # ns per sample
UPSAMPLE_FACTOR       = 40

F_LO          = 0.070            # GHz  (35 MHz)  −3 dB turn-on
F_HI          = 0.240            # GHz  (240 MHz) −3 dB cut-off
TRANSITION_BW = 0.020            # GHz  (20 MHz half-width on each edge)

DIRECTORY = "/mnt/labdata/chicago-rnog-system-response-2024/lab_measurements/labdata/"
DEEP_FILES = [
    "fullchain_deep_channel2_lowthreshon_fastimpulse.json",
    "fullchain_deep_channel2_lowthreshon_fastimpulse+6dB.json",
    "fullchain_deep_channel9_lowthreshon_fastimpulse+6dB.json",
    "fullchain_deep_channel11_lowthreshon_fastimpulse+6dB.json"
]
LABELS = ["ch2_2x_amp", "ch2", "ch9", "ch10"]

# ─── helpers ────────────────────────────────────────────────────────────────
def load_radiant_wfs(path, thr=180):
    """Return Waveform objects whose peak-to-peak exceeds threshold."""
    with open(path) as fh:
        raw = json.load(fh)

    keep = []
    for ev in raw:
        sig = np.asarray(ev["radiant_waveforms"], dtype=float)  # ensure float
        if sig.ptp() > thr and 40 < np.argmax(np.abs(sig)) < 2000:
            sig -= sig.mean()                                   # DC-remove
            keep.append(waveform.Waveform(sig,
                                          sampling_rate=1./RADIANT_SAMPLING_RATE))
    return keep

def make_avg_wf(waves, upsamp=UPSAMPLE_FACTOR):
    """FFT-align (cross-corr), up-sample in freq, and average."""
    avg = waves[0]
    avg.fft(); avg.upsampleFreqDomain(upsamp)
    for w in waves[1:]:
        w.fft(); w.upsampleFreqDomain(upsamp)
        delay = int(np.argmax(w.crossCorrelate(avg)) - len(w.voltage)/2)
        w.voltage = np.roll(w.voltage, -delay)
        avg.voltage += w.voltage
    avg.voltage /= len(waves)
    return avg

def smooth_bandpass_filter(wf, f_lo=F_LO, f_hi=F_HI, bw=TRANSITION_BW):
    """
    Raised-cosine band-pass: unity in [f_lo+bw, f_hi-bw],
    zero below f_lo-bw and above f_hi+bw, cosine tapers in between.
    """
    wf.fft()
    f = wf.freq                                         # GHz
    gain = np.zeros_like(f)

    lo1, lo2 = f_lo - bw, f_lo + bw
    hi1, hi2 = f_hi - bw, f_hi + bw

    # flat pass-band
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

# ─── main processing ────────────────────────────────────────────────────────
avg_resp = []

for fname in DEEP_FILES:
    thr = 180
    waves = load_radiant_wfs(DIRECTORY + fname, thr)
    avg   = make_avg_wf(waves)

    # centre, baseline, window, pre-trigger blank
    avg.voltage = np.roll(avg.voltage,
                          -int(np.argmax(avg.voltage) - len(avg.voltage)/2))
    avg.medianSubtract()
    avg.voltage = rxtx.window(avg.voltage, 20_000)
    avg.voltage[:np.where(avg.time > 415)[0][0]] = 0.0

    # smooth band-pass
    avg = smooth_bandpass_filter(avg)
    avg_resp.append(avg)

# ─── JSON output ────────────────────────────────────────────────────────────
deep_ir = {"time": avg_resp[0].time.tolist()}
for wf, key in zip(avg_resp, LABELS):
    deep_ir[key] = (wf.voltage / np.max(np.abs(wf.voltage))).tolist()

with open("deep_impulse_responses_bandpass70-240.json", "w") as fh:
    json.dump(deep_ir, fh, indent=2)

print("✓ deep_impulse_responses_bandpass70-240.json written.")
