import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy.optimize import curve_fit


# Constants
SNR_slope =0.2977818184056914  # Slope for SNR calculation

# Load data
json_path = Path("scan_over_20_angles_fine.json")
with json_path.open() as f:
    data = json.load(f)



def sigmoid(x, x0, k):
    return 1 / (1 + np.exp(-k * (x - x0)))

def fit_and_plot_sigmoid(x, y, ax):
    """Fit a sigmoid and plot it."""
    p0 = [np.median(x), 1.0]
    popt, _ = curve_fit(sigmoid, x, y, p0, maxfev=10000)
    x_fit = np.linspace(np.min(x), np.max(x), 300)
    y_fit = sigmoid(x_fit, *popt)
    ax.plot(x_fit, y_fit, '-', label=f'Sigmoid Fit\n$x_0$={popt[0]:.2f}, k={popt[1]:.2f}')
    ax.axhline(y=0.5, color='r', linestyle='--', label='50% Efficiency')
    ax.axvline(x=popt[0], color='g', linestyle='--', label=f'SNR @ 50% Eff.\n({popt[0]:.2f})')
    return popt


# Organize data by angle
angle_data = {}
for entry in data:
    angle = entry["angle_deg"]
    snr = SNR_slope * entry["attenuation_percent"]
    eff = entry["efficiency"]
    if angle not in angle_data:
        angle_data[angle] = {"snr": [], "eff": []}
    angle_data[angle]["snr"].append(snr)
    angle_data[angle]["eff"].append(eff)

sigmoid_params = {}
angles_list = sorted(angle_data.keys())
mid_points = []

for angle, values in angle_data.items():
    x = np.array(values["snr"])
    y = np.array(values["eff"])
    # Binomial error bars: sqrt(p*(1-p)/n), assuming n=20 (or set your actual n)
    n = 1000  # Change this to your actual number of trials per point if different
    # Ensure y is within [0, 1] and n > 0 to avoid invalid sqrt or division by zero
    y_clipped = np.clip(y, 0, 1)
    if n > 0:
        yerr = np.sqrt(y_clipped * (1 - y_clipped) / n)
    else:
        yerr = np.zeros_like(y)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.errorbar(x, y, yerr=yerr, fmt='o', label=f"Data (Angle = {angle}°)", capsize=3)
    popt = fit_and_plot_sigmoid(x, y, ax)
    sigmoid_params[angle] = popt
    mid_points.append(popt[0])
    ax.set_xlabel("Predicted SNR")
    ax.set_ylabel("Efficiency")
    ax.set_title(f"Efficiency vs SNR at {angle}° with Sigmoid Fit")
    #ax.set_xlim(1,6 )
    ax.set_ylim(0, 1.1)
    ax.grid(True)
    ax.legend()
    plt.tight_layout()
    filename = f"efficiency_vs_SNR_angle_{int(angle):+03d}.png"
    plt.savefig(filename, dpi=300)
    plt.close()

plt.plot(angles_list, mid_points, marker='o', linestyle='-', color='b')
plt.xlabel("Angle (degrees)")
plt.ylabel("SNR at 50% Efficiency")
plt.title("SNR at 50% Efficiency vs Angle")
plt.grid(True)
plt.tight_layout()
plt.savefig("SNR_at_50_percent_efficiency_vs_angle_fine.png", dpi=300)