#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import json, random
from pathlib import Path
from scipy.optimize import curve_fit

# bring in your simulation helpers
from sim_functions import (
    make_full_signal_angle,
    find_triggers,
)

# ===================== USER CONFIG =====================
# Sampling and simulation window
SAMPLING_RATE   = 0.472      # GHz
TIME_STEP       = 1.0 / SAMPLING_RATE
NOISE_EQUALIZE  = 5          # ADC RMS of noise
MAX_SIGNAL      = 4095       # ADC
WINDOW_SIZE     = 18.75*1e6    # MHz
N_WINDOWS       = 3
SIMULATION_DURATION_NS = N_WINDOWS / WINDOW_SIZE * 1e9
SIMULATION_DURATION_SAMPLES = int(SIMULATION_DURATION_NS / TIME_STEP) + 1
N_CHANNELS      = 4

# Trigger configuration
THRESHOLD_V     = [18, 21, 19, 21]   # per-channel thresholds in ADC
N_REQ           = 2                  # coincidence requirement
COINC_NS        = SIMULATION_DURATION_NS

# Scan settings
ANGLES_DEG      = np.arange(-2, 50, 1)      # angles to scan
# Keep your finer spacing between 10 and 20, otherwise step 2
PULSE_AMPLITUDES = np.concatenate([
    np.arange(6, 12, 2),
    np.arange(12, 21, 0.7),
    np.arange(22, 36, 2),
])

SCAN_RATE       = 150   # repeats per amplitude

# I/O
IMPULSE_JSON    = Path("/home/shamshassiki/Shams_Analyzing_scripts/Trigger_simulation_and_tests/jsons/impulse_response_Freauency_35_240.json")
PULSE_JSON      = Path("/home/shamshassiki/Shams_Analyzing_scripts/Trigger_simulation_and_tests/jsons/upsampled_2filter_pulse_example.json")

FINAL_PNG       = "hi_lo_50pct_efficiency_vs_angle_half_full_scan.png"
SAVE_PER_ANGLE  = False
PER_ANGLE_PREFIX= "hi_lo_passfrac_vs_snr_angle_AT0_2"


# =======================================================

# ---------- load and prep the template pulse ----------
with PULSE_JSON.open() as f:
    pulse_data = json.load(f)

pulse_voltage = np.array(pulse_data["avg_wave"])
pulse_time    = np.array(pulse_data["t_axis_ns"])

# crop and normalize like your originals
pulse_start_time, pulse_end_time = 450, 570
mask = (pulse_time >= pulse_start_time) & (pulse_time <= pulse_end_time)
pulse_voltage = pulse_voltage[mask]
pulse_time    = pulse_time[mask]
pulse_voltage = pulse_voltage / np.max(pulse_voltage)
pulse_time    = pulse_time - pulse_time[0]   # start from 0 ns

# ---------- helpers ----------
def sigmoid(x, a, b):
    return 1.0 / (1.0 + np.exp(-a * (x - b)))

def fit_sigmoid_get_b(snr, passfrac):
    # robust initial guesses
    xmid = np.median(snr)
    try:
        popt, _ = curve_fit(sigmoid, snr, passfrac, p0=[1.0, xmid], maxfev=10000)
        a, b = popt
    except Exception:
        # fallback if fit struggles: pick the SNR closest to 0.5 crossing by interpolation
        order = np.argsort(snr)
        snr_s = np.array(snr)[order]
        pf_s  = np.array(passfrac)[order]
        # simple linear interp to y=0.5
        b = np.interp(0.5, pf_s, snr_s)
        a = 1.0
    return a, b

def run_scan_for_angle(angle_deg):
    """
    For a fixed angle:
      - scan amplitudes
      - run SCAN_RATE realisations per amplitude
      - return SNR values, pass fractions, and the fit params a, b
    """
    pass_fraction, SNR_values = [], []

    for k, amp in enumerate(PULSE_AMPLITUDES):
        coinc = 0
        # progress hint
        print(f"\r  angle {angle_deg:+.0f}°  amp {k+1}/{len(PULSE_AMPLITUDES)}", end="")

        for scan_idx in range(SCAN_RATE):
            # one shared start seed so pulses are aligned across channels,
            # then per-channel geometric delay is added inside make_full_signal_angle
            start_seed = random.uniform(0, TIME_STEP)

            channel_signals = [[] for _ in range(N_CHANNELS)]
            time_start = scan_idx * SIMULATION_DURATION_NS

            for ch in range(N_CHANNELS):
                t, channel_signals[ch] = make_full_signal_angle(
                    impulse_json_path=IMPULSE_JSON,
                    SIMULATION_DURATION_NS=SIMULATION_DURATION_NS,
                    SAMPLING_RATE=SAMPLING_RATE,
                    NOISE_EQUALIZE=NOISE_EQUALIZE,
                    pulse_voltage=pulse_voltage,
                    pulse_time=pulse_time,
                    time_step=TIME_STEP,
                    simulation_duration_samples=SIMULATION_DURATION_SAMPLES,
                    amplitude_scale=amp,
                    max_signal=MAX_SIGNAL,
                    angle=angle_deg,
                    delay_seed=start_seed,
                    channel_index=ch
                )

            time_axis = t + time_start
            snr = amp / NOISE_EQUALIZE
            triggers = find_triggers(channel_signals, time_axis,
                                     threshold=THRESHOLD_V,
                                     coincidence_ns=COINC_NS,
                                     n_channels_required=N_REQ)
            if len(triggers) > 0:
                coinc += 1

        pass_fraction.append(coinc / SCAN_RATE)
        SNR_values.append(snr)

    # fit sigmoid to get 50% efficiency point
    a, b = fit_sigmoid_get_b(SNR_values, pass_fraction)
    return np.array(SNR_values), np.array(pass_fraction), a, b

# ---------- main loop over angles ----------
snr50_by_angle = []
for i, ang in enumerate(ANGLES_DEG):
    print(f"\nScanning angle {ang:+.0f} deg...")
    SNR_vals, pass_frac, a, b = run_scan_for_angle(ang)
    snr50_by_angle.append((ang, b))

    if SAVE_PER_ANGLE:
        plt.figure(figsize=(9, 6))
        plt.plot(SNR_vals, pass_frac, "o", label="Pass fraction")
        xfine = np.linspace(min(SNR_vals), max(SNR_vals), 400)
        plt.plot(xfine, sigmoid(xfine, a, b), "--", label="Sigmoid fit")
        plt.axhline(0.5, color="r", linestyle="--", linewidth=1)
        plt.axvline(b,   color="g", linestyle="--", linewidth=1,
                    label=f"50% eff SNR = {b:.2f}")
        plt.title(f"Hi-Lo trigger efficiency — angle {ang:+.0f}°")
        plt.xlabel("SNR")
        plt.ylabel("Pass fraction")
        plt.grid(True, alpha=0.4)
        plt.legend()
        out = f"{PER_ANGLE_PREFIX}_{ang:+.0f}deg.png".replace("+", "p").replace("-", "m")
        plt.tight_layout()
        plt.savefig(out, dpi=200)
        plt.close()

# ---------- final plot: 50% efficiency vs angle ----------
angles, snr50 = map(np.array, zip(*snr50_by_angle))
order = np.argsort(angles)
angles = angles[order]
snr50   = snr50[order]

plt.figure(figsize=(9, 6))
plt.plot(angles, snr50, "o-", label="50% efficiency SNR")
plt.title("Hi-Lo 50% efficiency vs angle")
plt.xlabel("Angle (deg)")
plt.ylabel("SNR at 50% efficiency")
plt.grid(True, alpha=0.4)
plt.legend()
plt.tight_layout()
plt.savefig(FINAL_PNG, dpi=220)
print(f"\nSaved final plot: {FINAL_PNG}")
