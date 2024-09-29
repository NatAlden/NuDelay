import argparse, json
import numpy as np

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import AutoMinorLocator

def get_window(tvals, sigvals, windowsize = [-15, 30], alpha = 1.5, noise=False, sigpeaktime=None, dt_downsample = 1):

    #If we just have a noise form, just pick a random point to get the window (here the middle of the waveform)
    if noise:
        t_peak = np.median(tvals)
    else:
        if sigpeaktime is None:
            t_peak = tvals[np.argmax(np.abs(sigvals))]
        else:
            t_peak = sigpeaktime

    window = np.zeros_like(tvals)

    mask = np.logical_and(tvals > t_peak + windowsize[0], tvals < t_peak + windowsize[1])
    window[mask] = 1.0

    dt = (tvals[1]-tvals[0])*dt_downsample
    windowtrange = tvals[mask][-1]-tvals[mask][0]
    #print(int(alpha * windowtrange/dt))
    cos_lobe = np.cos(np.linspace(-np.pi/2, np.pi/2, int(alpha * windowtrange/dt)))
    window = np.convolve(window, cos_lobe, mode = "same")

    window /= np.max(window)
    
    assert(len(window) == len(tvals))
    
    return window

def get_windowed_absfft(t, wf, windowsize = [-15, 30], noise=False, ax=None):

    N = len(wf)
    
    sigvals_windowed = wf * get_window(t, wf, windowsize = windowsize, noise=noise)
    
    if ax is not None:
        ax.plot(t, sigvals_windowed)
        ax.plot(t, get_window(t, wf, windowsize = windowsize, noise=noise))

    evt_fft = np.fft.rfft(sigvals_windowed)#/np.sqrt(2)
    evt_freqs = np.fft.rfftfreq(len(sigvals_windowed), t[1] - t[0])*10**3  #convert to units of MHz
    absfft = np.abs(evt_fft)  #/N

    #print(N, evt_freqs[1]-evt_freqs[0])
    #print(max(absfft))
    return evt_freqs, absfft


def plot_impulse_response(inpath, outpath, time_key = "time",                          
                          # signal_keys = ['v3_ch8_60dB', 'v3_ch8_60dB_xcheck', 'v3_ch8_62dB', 'v3_ch8_62dB_xcheck', 'v3_ch4_62dB', 'v3_ch1_62dB', 'v3_ch3_62dB'],
                          signal_keys = ['v3_ch8_62dB', 'v3_ch4_62dB', 'v3_ch1_62dB', 'v3_ch3_62dB', 'v3_ch23_62dB'],
                          fs = 13):

    with open(inpath, 'r') as infile:
        imp_data = json.load(infile)

    tvals = np.array(imp_data[time_key])

    fig = plt.figure(figsize = (6, 6))#, layout = "constrained")
    gs = GridSpec(2, 1, figure = fig)
    ax = fig.add_subplot(gs[0])

    ax_freq = fig.add_subplot(gs[1])

    for signal_key in signal_keys:
        cur_tvals = tvals - tvals[np.argmax(np.abs(imp_data[signal_key]))]
        ax.plot(cur_tvals, imp_data[signal_key], label = signal_key, lw = 1)

        freq, absfft = get_windowed_absfft(cur_tvals, imp_data[signal_key], windowsize = [-10, 30])
        ax_freq.plot(freq, absfft/max(absfft), label = signal_key, lw = 1)

    ax_freq.set_xlim([0, 1000])
    ax_freq.set_xlabel("Frequency [MHz]")
    ax_freq.set_ylabel("Amplitude [A.U.]")
    ax_freq.set_ylim([0, 1.5])
    ax_freq.legend(frameon = False, ncol = 2)

    ax.set_xlim(-10, 50)
    ax.legend(frameon = False, ncol = 2)
    ax.set_xlabel("Time [ns]", fontsize = fs)
    ax.set_ylabel("Response [norm.]", fontsize = fs)
   
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.tick_params(axis = "y", direction = "in", which = "both", left = True, right = True, labelsize = fs)
    ax.tick_params(axis = "x", direction = "in", which = "both", bottom = True, top = True, labelsize = fs)

    plt.tight_layout()
    fig.savefig(outpath)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required = True, action = "store", dest = "inpath")
    parser.add_argument("--outpath", required = True, action = "store", dest = "outpath")
    args = vars(parser.parse_args())

    plot_impulse_response(**args)
