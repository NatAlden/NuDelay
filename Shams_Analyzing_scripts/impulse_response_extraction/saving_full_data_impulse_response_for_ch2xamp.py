#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process deep-chain waveforms, apply a smooth 35–240 MHz band-pass,
and save the complex one-sided spectrum (real & imag) for the
*ch2 × 2-amp* channel to:

    full_data_spectrum_impulse_response_for_ch2_2x_amp.json
"""

import json
from pathlib import Path
import numpy as np
import tools.waveform as waveform
import vpol_txrx as rxtx

# ───────────────────────────────── Constants ───────────────────────────────
RADIANT_SAMPLING_RATE = 2.400    # ns per sample
UPSAMPLE_FACTOR       = 40

F_LO, F_HI            = 0.035, 0.240   # GHz  (–3 dB edges)
TRANSITION_BW         = 0.020          # GHz  (raised-cos half-width)

DATA_DIR = Path("/mnt/labdata/chicago-rnog-system-response-2024/lab_measurements/labdata/")
DEEP_FILES = [
    "fullchain_deep_channel2_lowthreshon_fastimpulse.json",      # ch2 ×2   ← we’ll keep this one
    "fullchain_deep_channel2_lowthreshon_fastimpulse+6dB.json",  # ch2
    "fullchain_deep_channel9_lowthreshon_fastimpulse+6dB.json",  # ch9
    "fullchain_deep_channel11_lowthreshon_fastimpulse+6dB.json"  # ch10
]

# ───────────────────────────────── Helpers ─────────────────────────────────
def load_radiant_wfs(path: Path, thr: float = 180):
    """Load RADIANT events → Waveform objects (mean-subtracted, quality cuts)."""
    events = json.loads(path.read_text())
    wfs = []
    for ev in events:
        sig = np.asarray(ev["radiant_waveforms"], float)
        sig -= sig.mean()
        idx = np.argmax(np.abs(sig))
        if sig.ptp() > thr and 40 < idx < 2000:
            wfs.append(waveform.Waveform(sig, sampling_rate=1./RADIANT_SAMPLING_RATE))
    return wfs

def make_avg_wf(waves, upsamp=UPSAMPLE_FACTOR):
    """FFT-align then average a list of Waveform objects."""
    avg = waves[0]; avg.fft(); avg.upsampleFreqDomain(upsamp)
    for w in waves[1:]:
        w.fft(); w.upsampleFreqDomain(upsamp)
        d = int(np.argmax(w.crossCorrelate(avg)) - len(w.voltage)/2)
        w.voltage = np.roll(w.voltage, -d)
        avg.voltage += w.voltage
    avg.voltage /= len(waves)
    return avg

def smooth_bandpass_filter(wf, f_lo=F_LO, f_hi=F_HI, bw=TRANSITION_BW):
    """Apply raised-cosine band-pass in place, keep phase."""
    wf.fft()
    f = wf.freq
    g = np.zeros_like(f)
    lo1, lo2 = f_lo - bw, f_lo + bw
    hi1, hi2 = f_hi - bw, f_hi + bw
    g[(f >= lo2) & (f <= hi1)] = 1.0
    g[(f > lo1) & (f < lo2)] = 0.5*(1-np.cos(np.pi*(f[(f>lo1)&(f<lo2)]-lo1)/(2*bw)))
    g[(f > hi1) & (f < hi2)] = 0.5*(1+np.cos(np.pi*(f[(f>hi1)&(f<hi2)]-hi1)/(2*bw)))
    wf.ampl *= g
    wf.voltage = np.fft.irfft(wf.ampl, n=len(wf.voltage))
    return wf

# ──────────────────────────── Processing (ch2 ×2) ──────────────────────────
# Process only the first file → ch2x2
waves = load_radiant_wfs(DATA_DIR / DEEP_FILES[0], thr=180)
avg   = make_avg_wf(waves)

# basic window / grooming
avg.voltage = np.roll(avg.voltage, -int(np.argmax(avg.voltage) - len(avg.voltage)/2))
avg.medianSubtract()
avg.voltage = rxtx.window(avg.voltage, 20_000)
avg.voltage[:np.where(avg.time > 415)[0][0]] = 0.0

# apply smooth 35–240 MHz band-pass
avg = smooth_bandpass_filter(avg)

# ───────────────────────── Save complex spectrum ───────────────────────────
spec_dict = {
    "freq_GHz": avg.freq.tolist(),     # positive-frequency axis
    "real":     avg.ampl.real.tolist(),
    "imag":     avg.ampl.imag.tolist()
}

out_file = "full_data_spectrum_impulse_response_for_ch2_2x_amp.json"
with open(out_file, "w") as fh:
    json.dump(spec_dict, fh, indent=2)

print(f"✓ {out_file} written (length = {len(avg.freq)} bins).")
