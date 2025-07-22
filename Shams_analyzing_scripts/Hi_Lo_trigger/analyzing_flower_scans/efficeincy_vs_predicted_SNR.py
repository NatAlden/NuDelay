import json
import matplotlib.pyplot as plt
import numpy as np

RATE = 1000  # Coincidence rate for normalization
SNR_slope = 0.2933456519033377 # SNR slope from the fit in get_SNR_from_p2p.py



# Load the data
with open("trigger_efficiency_curve_only_coinc.json", "r") as f:
    data = json.load(f)

# Extract attenuation_percent and corresponding peak_to_peak values
attenuations = []
average_SNR = []
efficiencies = []
for entry in data:
    SNR = []
    
    att_percent= entry["attenuation_percent"]
    attenuations.append(att_percent)

    average_SNR.append(SNR_slope * att_percent)  # Calculate SNR from attenuation percent

    eff = entry["coincidence_rate"]/ RATE  # Convert to efficiency
    efficiencies.append(eff)
    

# Plot
plt.figure(figsize=(6, 6))
plt.plot(average_SNR, efficiencies, marker='o')
plt.axhline(y=0.5, color='r', linestyle='--', label='50% Efficiency Threshold')

#SNR_50 = np.interp(0.5, efficiencies[(average_SNR > 4) & (average_SNR < 5)], average_SNR[(average_SNR > 4) & (average_SNR < 5)])

mask = (np.array(average_SNR) >1) & (np.array(average_SNR) < 5)
SNR_50 = np.interp(0.5, np.sort(np.array(efficiencies)[mask]), np.sort(np.array(average_SNR)[mask]))
print(SNR_50)
plt.axvline(x=SNR_50, color='g', linestyle='--', label='SNR at 50% Efficiency')

plt.legend()
#plt.xticks(np.arange(3, 6.1, 0.2))
#plt.yticks(np.arange(0, 1.1, 0.1))
plt.xlabel("Predicted SNR")
plt.ylabel("Efficiency")
plt.title("Trigger Efficiency Curve")
plt.grid(True)
plt.xlim(1, 6)  # Set x-axis limit
plt.ylim(0, 1.1)  # Set y-axis limit
plt.tight_layout()
plt.savefig("trigger_efficiency_curve_detailed_predicted_SNR.png", dpi=300)
plt.show()



