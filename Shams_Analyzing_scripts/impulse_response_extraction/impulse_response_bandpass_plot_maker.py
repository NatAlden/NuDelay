#!/usr/bin/env python3
"""
Deep-chain impulse responses with raised-cosine band-pass 35–240 MHz.
Outputs:
  • deep_impulse_responses_bandpass35-240.json
  • bandpass35-240_frequency_domain.png   ← NEW
"""

import json, numpy as np, matplotlib.pyplot as plt
import tools.waveform as waveform
import vpol_txrx as rxtx

# ─── constants ──────────────────────────────────────────────────────────────
RADIANT_SAMPLING_RATE = 2.400
UPSAMPLE_FACTOR       = 40

F_LO, F_HI            = 0.035, 0.240      # GHz
TRANSITION_BW         = 0.020             # GHz (roll-off half-width)

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
    f = wf.freq
    gain = np.zeros_like(f)
    lo1, lo2 = f_lo - bw, f_lo + bw
    hi1, hi2 = f_hi - bw, f_hi + bw
    gain[(f >= lo2) & (f <= hi1)] = 1.0
    lo_mask = (f > lo1) & (f < lo2)
    gain[lo_mask] = 0.5 * (1 - np.cos(np.pi * (f[lo_mask] - lo1)/(2*bw)))
    hi_mask = (f > hi1) & (f < hi2)
    gain[hi_mask] = 0.5 * (1 + np.cos(np.pi * (f[hi_mask] - hi1)/(2*bw)))
    wf.ampl *= gain
    wf.voltage = np.fft.irfft(wf.ampl, n=len(wf.voltage))
    return wf

# ─── main processing ────────────────────────────────────────────────────────
avg_resp = []
for fname in DEEP_FILES:
    waves = load_radiant_wfs(DIRECTORY + fname, thr=180)
    avg   = make_avg_wf(waves)
    avg.voltage = np.roll(avg.voltage, -int(np.argmax(avg.voltage)-len(avg.voltage)/2))
    avg.medianSubtract()
    avg.voltage = rxtx.window(avg.voltage, 20_000)
    avg.voltage[:np.where(avg.time > 415)[0][0]] = 0.0
    avg = smooth_bandpass_filter(avg)
    avg_resp.append(avg)

# ─── JSON output ────────────────────────────────────────────────────────────
deep_ir = {"time": avg_resp[0].time.tolist()}
for wf, key in zip(avg_resp, LABELS):
    deep_ir[key] = (wf.voltage / np.max(np.abs(wf.voltage))).tolist()


# ─── frequency-domain quick-look plot (NEW) ─────────────────────────────────
plt.figure(figsize=(8,4))
for wf, lab in zip(avg_resp, LABELS):
    plt.plot(wf.freq, np.abs(wf.ampl)/np.max(np.abs(wf.ampl)), lw=1, label=lab)
plt.xlabel("Frequency (GHz)")
plt.ylabel("Normalised amplitude")
plt.title("Deep-chain spectra (smooth 35–240 MHz band-pass)")
plt.xlim(0, 0.5)
plt.grid(True, lw=0.3); plt.legend(ncol=2, fontsize=8)
plt.tight_layout()
plt.savefig("bandpass35-240_frequency_domain_newest.png", dpi=200)

print("✓ bandpass35-240_frequency_domain.png saved.")
