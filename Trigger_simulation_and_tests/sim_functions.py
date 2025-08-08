import json
import numpy as np
from pathlib import Path    
import matplotlib.pyplot as plt
import random
import math
import os
import sys


def make_band_limited_noise(json_path,
                            channel_key="ch0",
                            window_ns=1000.0,  # length of the output trace in ns
                            adc_rate_ghz=0.472,   # hardware sampling rate
                            oversample=1,         # use >1 for fractional-ns step
                            target_rms_mV=1.0,
                            rng=None):
    """
    Return (time_ns, noise_mV) for one random noise realisation whose
    spectrum follows the magnitude in `json_path[channel_key]`.

    Parameters
    ----------
    json_path : str | Path
        Path to impulse-response JSON containing keys 'freq_GHz' + channels.
    channel_key : str
        Which channel’s magnitude to use as the band-pass shape.
    window_ns : float
        Length of the output trace in nanoseconds.
    adc_rate_ghz : float
        Native ADC rate of the system (GHz).
    oversample : int
        Upsampling factor applied before the FFT (Δt = 1/(adc_rate*oversample)).
    target_rms_mV : float
        RMS of the returned waveform, in millivolts.
    rng : numpy.random.Generator | None
        Source of randomness (defaults to np.random.default_rng()).

    Returns
    -------
    time_ns : 1-D ndarray
        Time axis in nanoseconds.
    noise_mV : 1-D ndarray
        Band-limited noise in millivolts, rms ≈ `target_rms_mV`.
    """
    # ---------- load magnitude response ------------
    data = json.loads(Path(json_path).read_text())
    freq_ref   = np.asarray(data["freq_GHz"])        # GHz
    mag_ref    = np.asarray(data[channel_key])

    # ---------- define FFT grid --------------------
    dt_ns  = 1.0 / (adc_rate_ghz * oversample)       # ns
    N      = int(round(window_ns / dt_ns))
    dt_s   = dt_ns * 1e-9
    freq_Hz = np.fft.rfftfreq(N, d=dt_s)
    freq_GHz = freq_Hz / 1e9

    # ---------- interpolate → Rayleigh σ -----------
    sigma = np.interp(freq_GHz, freq_ref, mag_ref, left=0.0, right=0.0)

    # ---------- draw random spectrum ---------------
    rng = rng or np.random.default_rng()
    amp   = rng.rayleigh(scale=sigma)
    phase = rng.uniform(0, 2*np.pi, size=amp.size)
    spec  = amp * np.exp(1j * phase)

    # ---------- IFFT to time domain ----------------
    noise = np.fft.irfft(spec, n=N)

    # ---------- normalise RMS ----------------------
    rms = np.sqrt(np.mean(noise ** 2)) or 1.0
    noise_mV = noise / rms * target_rms_mV

    time_ns = np.arange(N) * dt_ns
    return time_ns, noise_mV

def generate_pulse (pulse_v, pulse_t , STEP, simulation_index_duration, amplitude_scale):
    start_time= random.uniform(0, STEP)
    start_index= np.argmin(np.where(pulse_t >= start_time)[0])
    pulse_indices= np.linspace(start_index, len(pulse_v)-1, simulation_index_duration, dtype=int)
    

    if pulse_indices[-1] > len(pulse_v):
        raise ValueError("Pulse exceeds total duration when placed at the specified start time.")

    signal = pulse_v[pulse_indices] * amplitude_scale  # Scale the pulse voltage
    return signal

def digitize_signal(signal, max_signal):
    """
    Digitize the signal to the ADC range.
    """
    digitized_signal = np.clip(signal, -max_signal//2, max_signal//2)
    return digitized_signal

def make_full_signal(impulse_json_path, SIMULATION_DURATION_NS, SAMPLING_RATE, NOISE_EQUALIZE,
                     pulse_voltage, pulse_time, time_step, simulation_duration_samples, amplitude_scale, max_signal):

    t, noise=make_band_limited_noise(
        impulse_json_path,
        "ch2_2x_amp",
        window_ns=SIMULATION_DURATION_NS,
        adc_rate_ghz=SAMPLING_RATE,
        oversample=1,
        target_rms_mV=NOISE_EQUALIZE,
    ) 
    
    pulse = generate_pulse(pulse_voltage, pulse_time, time_step, simulation_duration_samples, amplitude_scale)
    full_signal = digitize_signal(noise + pulse, max_signal)
    full_signal = full_signal[:simulation_duration_samples]  # Ensure the signal length matches the
    return t, full_signal

def plot_4_channels_signals(time_axis, channel_signals, title="4 Channels Signals"):
    """
    Plot signals from 4 channels on the same graph.
    
    Parameters
    ----------
    time_axis : array-like
        Time stamps (ns) corresponding to the samples.
    channel_signals : list of list of float
        Each sublist contains signal values for one channel.
    title : str, optional
        Title of the plot.
    """
    plt.figure(figsize=(12, 6))
    for ch, signal in enumerate(channel_signals):
        plt.plot(time_axis, signal, label=f'Channel {ch+1}')
    
    plt.title(title)
    plt.xlabel('Time (ns)')
    plt.ylabel('Amplitude (ADC counts)')
    plt.legend()
    plt.grid()
    full_title = f"{title} - {int(time_axis[0])} ns to {int(time_axis[-1])} ns"
    plt.savefig(f"{full_title}.png")

def find_triggers(channel_signals, time_axis, *,            # ← positional, keyword-only
                  threshold, coincidence_ns=160,
                  n_channels_required=2):
    """
    Detect coincidence triggers.

    Parameters
    ----------
    channel_signals : list[list[float]]
        One list/array per channel, same length as time_axis.
    time_axis : array-like
        Time stamps (ns) corresponding to the samples.
    threshold : float
        Voltage threshold for a channel to count as "hit".
    coincidence_ns : float, default 160
        Width of coincidence window (ns).  All hits whose times fall
        within ±(coincidence_ns/2) of the trigger centre are grouped.
    n_channels_required : int, default 2
        Minimum distinct channels required to declare a trigger.

    Returns
    -------
    triggers : list[dict]
        Each dict: {"t_trigger": float, "channels": list[int]}
    """
    half_window = coincidence_ns / 2.0

    # -------- 1. collect (time, channel) hits -------------------------------
    hits_t = []
    hits_ch = []
    for ch, sig in enumerate(channel_signals):
        sig = np.asarray(sig)
        idx = np.nonzero(sig > threshold[ch])[0]      # indices where above threshold
        hits_t.extend(time_axis[idx])
        hits_ch.extend([ch] * len(idx))

    if not hits_t:
        return []                                 # no hits → no triggers

    # -------- 2. sort hits by time ------------------------------------------
    hits = sorted(zip(hits_t, hits_ch))           # tuples (t, ch)

    # -------- 3. walk through hits, build coincidence groups ---------------
    triggers = []
    i = 0
    while i < len(hits):
        t0   = hits[i][0]                         # start of new group
        group_ch = {hits[i][1]}
        j = i + 1
        while j < len(hits) and hits[j][0] - t0 <= half_window:
            group_ch.add(hits[j][1])
            j += 1

        if len(group_ch) >= n_channels_required:
            triggers.append({"t_trigger": t0, "channels": sorted(group_ch)})

        # move i to first hit outside the current window
        while i < len(hits) and hits[i][0] - t0 <= half_window:
            i += 1

    return triggers