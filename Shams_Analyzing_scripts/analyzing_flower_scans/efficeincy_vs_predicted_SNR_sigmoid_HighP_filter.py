import json
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

RATE = 1000  # Coincidence rate for normalization
SNR_slope =  0.28004548909338794  # SNR slope from the fit in get_SNR_from_p2p.py

def sigmoid(x, x0, k):
    """Sigmoid function for fitting."""
    return 1 / (1 + np.exp(-k * (x - x0)))

def fit_and_plot_sigmoid(x, y, ax=None):
    """Fit a sigmoid to the data and plot both data and fit."""
    # Initial guess for parameters: midpoint and slope
    p0 = [np.median(x), 1.0]
    popt, _ = curve_fit(sigmoid, x, y, p0, maxfev=10000)
    x_fit = np.linspace(np.min(x), np.max(x), 200)
    y_fit = sigmoid(x_fit, *popt)
    if ax is None:
        ax = plt.gca()
    
    ax.plot(x_fit, y_fit, '-', label=f'Sigmoid Fit\n$x_0$={popt[0]:.2f}, k={popt[1]:.2f}')
    return popt

# Load the data
with open("trigger_efficiency_mode_1_HighP_filters.json", "r") as f:
    data = json.load(f)

# Extract attenuation_percent and corresponding peak_to_peak values
attenuations = []
average_SNR = []
efficiencies = []
for entry in data:
    att_percent = entry["attenuation_percent"]
    attenuations.append(att_percent)
    average_SNR.append(SNR_slope * att_percent)  # Calculate SNR from attenuation percent
    eff = entry["coincidence_rate"] / RATE  # Convert to efficiency
    efficiencies.append(eff)

average_SNR = np.array(average_SNR)
efficiencies = np.array(efficiencies)

# Plot
fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(average_SNR, efficiencies, marker='o', linestyle='', label='Data')
popt = fit_and_plot_sigmoid(average_SNR, efficiencies, ax=ax)
ax.axhline(y=0.5, color='r', linestyle='--', label='50% Efficiency Threshold')
ax.axvline(x=popt[0], color='g', linestyle='--', label=f'SNR at 50% Eff. ({popt[0]:.2f})')

ax.legend()
ax.set_xlabel("Predicted SNR")
ax.set_ylabel("Efficiency")
ax.set_title("Trigger Efficiency Curve with Sigmoid Fit (HighP filter Mode 1)")
ax.grid(True)
ax.set_xlim(1, 6)
ax.set_ylim(0, 1.1)
plt.tight_layout()
plt.savefig("trigger_efficiency_curve_detailed_predicted_SNR_sigmoid_HighP_mod1.png", dpi=300)