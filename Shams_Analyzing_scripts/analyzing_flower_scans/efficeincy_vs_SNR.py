import json
import matplotlib.pyplot as plt
import numpy as np

RATE = 1000  # Coincidence rate for normalization
RMS=[5.20520436366991, 4.6083874456991945, 5.227988702537071, 5.868187568757097]
# Load the data
with open("trigger_efficiency_curve_analysis.json", "r") as f:
    data = json.load(f)

# Extract attenuation_percent and corresponding peak_to_peak values
attenuations = []
average_SNR = []
efficiencies = []
for entry in data:
    SNR = []
    att = entry["attenuation_scale"]
    eff = entry["coincidence_rate"]/ RATE  # Convert to efficiency
    efficiencies.append(eff)
    p2p = entry["peak_to_peak"]
    if len(p2p) == 4:
        attenuations.append(att)
        for i in range(4):
            SNR.append(p2p[i]/(RMS[i]*2))  # Normalize by RMS

    average_SNR.append(np.mean(SNR))  # Average SNR across channels

# Plot
plt.figure(figsize=(6, 6))
plt.plot(average_SNR, efficiencies, marker='o')
plt.axhline(y=0.5, color='r', linestyle='--', label='50% Efficiency Threshold')

#SNR_50 = np.interp(0.5, efficiencies[(average_SNR > 4) & (average_SNR < 5)], average_SNR[(average_SNR > 4) & (average_SNR < 5)])

mask = (np.array(average_SNR) > 4) & (np.array(average_SNR) < 5)
SNR_50 = np.interp(0.5, np.sort(np.array(efficiencies)[mask]), np.sort(np.array(average_SNR)[mask]))
print(SNR_50)
plt.axvline(x=SNR_50, color='g', linestyle='--', label='SNR at 50% Efficiency')

plt.legend()
plt.xticks(np.arange(3, 6.1, 0.2))
plt.yticks(np.arange(0, 1.1, 0.1))
plt.xlabel("Average SNR")
plt.ylabel("Efficiency")
plt.title("Trigger Efficiency Curve")
plt.grid(True)
plt.xlim(3, 6)  # Set x-axis limit
plt.ylim(0, 1)  # Set y-axis limit
plt.tight_layout()
plt.savefig("trigger_efficiency_curve_detailed_4.png")
plt.show()



