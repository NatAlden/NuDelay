import json
import matplotlib.pyplot as plt

sim_file= "simulated_data.json"
patt_Highlow_array_scan = "patt_HiLo_scan_pulser_drop_30_150.json"
patt_phased_array_scan = "patt_phased_array_scan_pulser_drop_30_150.json"

# Load the JSON data
with open(sim_file, 'r') as f:
    data = json.load(f)

with open(patt_Highlow_array_scan, 'r') as f:
    patt_Highlow_data = json.load(f)

with open(patt_phased_array_scan, 'r') as f:
    patt_phased_data = json.load(f)



# Extract lists
sim_angle_list = [entry["angle_deg"] for entry in data]
sim_Highlow_list = [entry["highlow_50"] for entry in data]
sim_phased_list = [entry["power_50"] for entry in data]

# Extract lists from Highlow and Phased data
patt_Highlow_angle_list = patt_Highlow_data["angles_list"]
patt_Highlow_mid_points = patt_Highlow_data["mid_points"]
patt_phased_angle_list = patt_phased_data["angles_list"]
patt_phased_mid_points = patt_phased_data["mid_points"]


beams = [
    -60.0, -45.11838005, -33.44299614, -23.18167437, -13.66170567,
    -4.51554582, 4.51554582, 13.66170567, 23.18167437, 33.44299614,
    45.11838005, 60.0
]

# Plotting
plt.errorbar(sim_angle_list, sim_phased_list, yerr=0.1, fmt='o', label='Simulated Phased Array', capsize=2)
plt.errorbar(sim_angle_list, sim_Highlow_list, yerr=0.1, fmt='s', label='Simulated Highlow', capsize=2)
plt.plot(patt_phased_angle_list, patt_phased_mid_points[::-1], 'v', label='PATT Phased Array pulser drop', color='orange')
plt.plot(patt_Highlow_angle_list, patt_Highlow_mid_points, 'x', label='PATT Highlow pulser drop', color='green')

for i, beam in enumerate(beams):
    plt.axvline(x=beam, color='green', linestyle=':', linewidth=0.7)
    plt.text(beam, plt.ylim()[1] * 0.55, f'beam {i}', color='green', rotation=90, va='top', ha='right', fontsize=7)

plt.xlabel("Angle [deg]")
plt.ylabel("SNR at 50% Efficiency")
plt.title("Simulated vs PATT pulser drop (30_150) Measured SNR at 50% Efficiency")
plt.legend( loc='upper left', fontsize=8)
plt.grid(True)
plt.ylim(1.8, 5.0)
plt.tight_layout()
plt.savefig("Simulated_vs_PATT_Measured_SNR_at_50_Efficiency_pulser_drop_delays_inverted.png", dpi=300)
plt.show()
