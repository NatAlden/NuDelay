import json
import matplotlib.pyplot as plt
import numpy as np

RATE = 1000  # Coincidence rate for normalization
#RMS= [5.20520436366991, 4.6083874456991945, 5.227988702537071, 5.868187568757097]
#RMS = [5.328636610698969, 5.92109679158174, 5.374270756281122, 5.970302973754305]
#RMS = [5.22822458631876, 5.908401755390233, 5.307190438989281, 5.9405500721252285]
#RMS = [5.256680058792767, 5.864466459798114, 5.287152033920513, 5.9001626038848345]
<<<<<<< HEAD
#RMS = [5.256479021631751, 6.042870621281024, 5.30402743242648, 5.9463751013136745]
RMS = [5.2802359111161845, 5.946562471813204, 5.279512943042054, 5.935232044632074]


# Load the data
with open("getting_SNR_Phased_07_28.json", "r") as f:
=======
RMS = [5.238772259022641, 5.881591570081945, 5.301073587963318, 5.905511131666297]

# Load the data
with open("getting_SNR_from_p2p_07_18.json", "r") as f:
>>>>>>> 0fafe307175edfea6198b25fd08db5dead253aca
    data = json.load(f)

# Extract attenuation_percent and corresponding peak_to_peak values
attenuations = []
average_SNR = []

for entry in data:
    SNR = []
    att =  entry["attenuation_scale"]
    att = 100*10**(-att/80)
    
    p2p = entry["peak_to_peak"]
    if len(p2p) == 4:
        attenuations.append(att)
        for i in range(4):
            SNR.append(p2p[i]/(RMS[i]*2))  # Normalize by RMS

    average_SNR.append(np.mean(SNR))  # Average SNR across channels


attenuations = np.array(attenuations)
average_SNR = np.array(average_SNR)
mask = (attenuations < 60) & (attenuations > 20)

fit_coeffs = np.polyfit(attenuations[mask], average_SNR[mask], 1)
fit_fn = np.poly1d(fit_coeffs)

# Generate extended x values for the fit line
fit_x = np.linspace(0, 90, 200)
fit_y = fit_fn(fit_x)
###########

x_masked = attenuations[mask]
y_masked = average_SNR[mask]
slope = np.sum(x_masked * y_masked) / np.sum(x_masked * x_masked)
fit_y = slope * fit_x  # fit_x already defined as np.linspace(0, 90, 200)
print(f"Calculated slope: {slope}")
# Plot
plt.figure(figsize=(6, 6))
plt.plot(attenuations, average_SNR, marker='o', label='All Data')
plt.plot(x_masked, y_masked, marker='o', color='red', label='Masked Data')
plt.plot(fit_x, fit_y, color='blue', linestyle='--', label='Linear Fit through (0,0)')

plt.xlabel("attenuation %")
plt.ylabel("p2p SNR (normalized by RMS)")
<<<<<<< HEAD
plt.title("p2p SNR vs Attenuation Percent double High Pass Filtered")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("getting_SNR_Phased_07_28.png" , dpi=300)
=======
plt.title("p2p SNR vs Attenuation Percent High Pass Filtered")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("p2p_SNR_vs_attenuation_fixed_07_18_5deg.png" , dpi=300)
>>>>>>> 0fafe307175edfea6198b25fd08db5dead253aca
plt.show()