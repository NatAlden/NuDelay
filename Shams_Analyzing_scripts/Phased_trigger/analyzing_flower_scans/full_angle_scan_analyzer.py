import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy.optimize import curve_fit


# Constants
SNR_slope = 0.2987923898864614  # Slope for SNR calculation

# Load data
json_path = Path("phased_full_detailed_scan_07_19_2filters.json")
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
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(x, y, 'o', label=f"Data (Angle = {angle}°)")
    popt = fit_and_plot_sigmoid(x, y, ax)
    sigmoid_params[angle] = popt
    mid_points.append(popt[0])
    ax.set_xlabel("Predicted SNR")
    ax.set_ylabel("Efficiency")
    ax.set_title(f"Efficiency vs SNR at {angle}° with phased trigger")
    ax.set_xlim(1,6 )
    ax.set_ylim(0, 1.1)
    ax.grid(True)
    ax.legend()
    plt.tight_layout()
    filename = f"efficiency_vs_SNR_angle_{int(angle):+03d}_phased_trigger.png"
    #plt.savefig(filename, dpi=300)
    plt.close()

beams = [
    -60.0, -45.11838005, -33.44299614, -23.18167437, -13.66170567,
    -4.51554582, 4.51554582, 13.66170567, 23.18167437, 33.44299614,
    45.11838005, 60.0
]

plt.plot(angles_list, mid_points, marker='o', markersize=4, linestyle='-', linewidth=1, color='black', alpha=0.7, label='Mid Points of Sigmoid Fits')
for i, beam in enumerate(beams):
    plt.axvline(x=beam, color='green', linestyle=':', linewidth=0.7)
    plt.text(beam, plt.ylim()[1] * 0.985, f'beam {i}', color='green', rotation=90, va='top', ha='right', fontsize=6)
plt.xlabel("Angle (degrees)")
plt.legend( loc='upper left', fontsize=8)
plt.ylabel("SNR at 50% Efficiency")
plt.title("SNR at 50% Efficiency vs Angle phased trigger full scan (both filters)_wrong_slope")
#plt.grid(True)
plt.tight_layout()
plt.savefig("50%_SNR_efficiency_vs_angle_full_scan_phased_array_2filters_wrong_slope.png", dpi=300)