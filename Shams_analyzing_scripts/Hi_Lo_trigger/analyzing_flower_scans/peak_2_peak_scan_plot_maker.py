import json
import matplotlib.pyplot as plt
import numpy as np


RMS=[5.20520436366991, 4.6083874456991945, 5.227988702537071, 5.868187568757097]
# Load the data
with open("peak_to_peak_coinc_analysis.json", "r") as f:
    data = json.load(f)

# Extract attenuation_percent and corresponding peak_to_peak values
attenuations = []
SNR = [[] for _ in range(4)]  # One list per channel

for entry in data:
    att = entry["attenuation_scale"]
     
    p2p = entry["peak_to_peak"]
    if len(p2p) == 4:
        attenuations.append(att)
        for i in range(4):
            SNR[i].append(p2p[i]/(RMS[i]*2))  # Normalize by RMS

# Plot
plt.figure(figsize=(12, 6))
labels = ["Channel A", "Channel B", "Channel C", "Channel D"]
attenuations =  10** (-np.array(attenuations)/(4 * 10)) 
for i in range(4):
    plt.plot(attenuations, SNR[i], label=labels[i], marker='o')

plt.xlabel("Attenuation Percentage (%)")
plt.ylabel("SNR")
plt.title("SNR vs Attenuation Percentage")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("SNR_vs_attenuation.png")
plt.show()
