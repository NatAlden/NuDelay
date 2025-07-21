#!/usr/bin/env python3
"""
Deep-chain impulse responses – frequency-domain version.
A smooth raised-cosine band-pass from 35 MHz to 240 MHz (20 MHz roll-off)
is applied, then the *filtered spectrum* (|FFT|) is saved to JSON:

    impulse_response_Freauency_35_240.json
"""

import json
import numpy as np
import tools.waveform as waveform
import vpol_txrx as rxtx

# ─── constants ──────────────────────────────────────────────────────────────
RADIANT_SAMPLING_RATE = 2.400   # ns per sample
UPSAMPLE_FACTOR       = 40

F_LO, F_HI            = 0.035, 0.240   # GHz
TRANSITION_BW         = 0.020          # GHz  (20 MHz half-width)

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
    with open(path) as fh:
        raw = json.load(fh)
    keep = []
    for ev in raw:
        sig = np.asarray(ev["radiant_waveforms"], dtype=float)
        if sig.ptp() > thr and 40 < np.argmax(np.abs(sig)) < 2000:
            sig -= sig.mean()
            keep.append(waveform.Waveform(sig, sampling_rate=1./RADIANT_SAMPLING_RATE))
    return keep

def make_avg_wf(waves, upsamp=UPSAMPLE_FACTOR):
    avg = waves[0]; avg.fft(); avg.upsampleFreqDomain(upsamp)
    for w in waves[1:]:
        w.fft(); w.upsampleFreqDomain(upsamp)
        delay = int(np.argmax(w.crossCorrelate(avg)) - len(w.voltage)/2)
        w.voltage = np.roll(w.voltage, -delay)
        avg.voltage += w.voltage
    avg.voltage /= len(waves)
    return avg

def smooth_bandpass_filter(wf, f_lo=F_LO, f_hi=F_HI, bw=TRANSITION_BW):
    wf.fft()
    f = wf.freq                                   # GHz
    gain = np.zeros_like(f)
    lo1, lo2 = f_lo - bw, f_lo + bw
    hi1, hi2 = f_hi - bw, f_hi + bw

    # pass-band + raised-cos transitions
    gain[(f >= lo2) & (f <= hi1)] = 1.0
    lo_mask = (f > lo1) & (f < lo2)
    gain[lo_mask] = 0.5 * (1 - np.cos(np.pi*(f[lo_mask]-lo1)/(2*bw)))
    hi_mask = (f > hi1) & (f < hi2)
    gain[hi_mask] = 0.5 * (1 + np.cos(np.pi*(f[hi_mask]-hi1)/(2*bw)))

    wf.ampl *= gain
    return wf                             # keep spectrum only

# ─── main processing ────────────────────────────────────────────────────────
avg_resp = []

for fname in DEEP_FILES:
    waves = load_radiant_wfs(DIRECTORY + fname, thr=180)
    avg   = make_avg_wf(waves)

    # centre, baseline, window, pre-trigger blank
    avg.voltage = np.roll(avg.voltage,
                          -int(np.argmax(avg.voltage)-len(avg.voltage)/2))
    avg.medianSubtract()
    avg.voltage = rxtx.window(avg.voltage, 20_000)
    avg.voltage[:np.where(avg.time > 415)[0][0]] = 0.0

    # obtain filtered spectrum
    avg = smooth_bandpass_filter(avg)
    avg_resp.append(avg)

# ─── JSON output : frequency domain ─────────────────────────────────────────
freq_GHz = avg_resp[0].freq.tolist()        # common freq axis

freq_ir = {"freq_GHz": freq_GHz}
for wf, key in zip(avg_resp, LABELS):
    # magnitude, normalised to channel peak (optional)
    mag = np.abs(wf.ampl)
    mag /= mag.max() if mag.max() > 0 else 1.0
    freq_ir[key] = mag.tolist()

with open("impulse_response_Freauency_35_240.json", "w") as fh:
    json.dump(freq_ir, fh, indent=2)

print("✓ impulse_response_Freauency_35_240.json written with frequency-domain data.")
