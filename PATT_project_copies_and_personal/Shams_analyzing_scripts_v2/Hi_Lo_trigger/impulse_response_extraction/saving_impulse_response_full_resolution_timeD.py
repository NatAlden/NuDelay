#!/usr/bin/env python3
import json, numpy as np, matplotlib.pyplot as plt
import tools.waveform as waveform
import vpol_txrx as rxtx
from pathlib import Path

# ─── constants & file ------------------------------------------------------ #
RADIANT_SAMPLING_RATE = 2.400   # ns per sample
UPSAMPLE_FACTOR       = 40

F_LO, F_HI            =  35,240 # 0.035, 0.240   # GHz
BW                    = 20          # GHz  (raised-cos halfwidth)

directory   = "/mnt/labdata/chicago-rnog-system-response-2024/lab_measurements/labdata/"
ch2x2_file  = "fullchain_deep_channel2_lowthreshon_fastimpulse.json"

# ─── helper: raised-cosine band-pass filter ------------------------------- #
def smooth_bandpass_filter(wf, f_lo, f_hi, bw):
    wf.fft()
    f = wf.freq
    gain = np.zeros_like(f)
    lo1, lo2 = f_lo-bw, f_lo+bw
    hi1, hi2 = f_hi-bw, f_hi+bw
    gain[(f >= lo2) & (f <= hi1)] = 1.0
    gain[(f > lo1) & (f < lo2)] = 0.5*(1-np.cos(np.pi*(f[(f>lo1)&(f<lo2)]-lo1)/(2*bw)))
    gain[(f > hi1) & (f < hi2)] = 0.5*(1+np.cos(np.pi*(f[(f>hi1)&(f<hi2)]-hi1)/(2*bw)))
    wf.ampl *= gain
    wf.voltage = np.fft.irfft(wf.ampl, n=len(wf.voltage))
    return wf

# ─── load waveforms, avg, filter ------------------------------------------ #
with open(Path(directory)/ch2x2_file) as fh:
    raw = json.load(fh)

waves = []
for ev in raw:
    sig = np.asarray(ev["radiant_waveforms"], float)
    sig -= sig.mean()
    idx = np.argmax(np.abs(sig))
    if sig.ptp() > 180 and 40 < idx < 2000:
        waves.append(waveform.Waveform(sig, sampling_rate=1./RADIANT_SAMPLING_RATE))

# average (FFT-aligned)
avg = waves[0]; avg.fft(); avg.upsampleFreqDomain(UPSAMPLE_FACTOR)
for w in waves[1:]:
    w.fft(); w.upsampleFreqDomain(UPSAMPLE_FACTOR)
    d = int(np.argmax(w.crossCorrelate(avg)) - len(w.voltage)/2)
    w.voltage = np.roll(w.voltage, -d)
    avg.voltage += w.voltage
avg.voltage /= len(waves)

# preprocess window, blank pre-trigger
avg.voltage = np.roll(avg.voltage, -int(np.argmax(avg.voltage)-len(avg.voltage)/2))
avg.medianSubtract()
avg.voltage = rxtx.window(avg.voltage, 20000)
avg.voltage[:np.where(avg.time > 415)[0][0]] = 0.0

# apply band-pass and keep spectrum
avg = smooth_bandpass_filter(avg, F_LO, F_HI, BW)

# ─── time-domain impulse reconstruction & centring ------------------------ #
impulse = np.fft.irfft(avg.ampl, n=len(avg.voltage))
center  = len(impulse)//2
impulse = np.roll(impulse, center - np.argmax(np.abs(impulse)))

# time axis (ns)
t_ns = (np.arange(len(impulse)) - center) * RADIANT_SAMPLING_RATE

# ─── plot & save ----------------------------------------------------------- #
plt.figure(figsize=(9,4))
plt.plot(t_ns, impulse/np.max(np.abs(impulse)), lw=1.2, label="ch2 ×2 amp")
plt.xlabel("time (ns)")
plt.ylabel("normalised amplitude")
plt.title("Centred impulse response • ch2×2 (35–240 MHz band-pass)")
plt.grid(True, lw=0.3)
plt.legend()
plt.xlim(-100, 100)

plt.tight_layout()
plt.savefig("test_1_.png", dpi=300)

# ─── save time-domain impulse to JSON ──────────────────────────────────────
impulse_dict = {
    "time_ns": t_ns.tolist(),              # centred time axis
    "ch2x2":   (impulse / np.max(np.abs(impulse))).tolist()
}

with open("full_impulse_response_wavefront.json", "w") as jf:
    json.dump(impulse_dict, jf, indent=2)

print("✓ full_impulse_response_wavefront.json written.")

