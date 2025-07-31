# PATT–FLOWER Scan Scripts

This directory contains the main scripts used to run communication-based scan tests between the PATT and the FLOWER devices. Each scan requires two scripts to run in tandem, one on the PATT (sender) and one on the FLOWER (receiver).

---

## 🔹 Communication Setup

- **PATT → FLOWER connection** is established over a shared local network.
- Make sure the IP addresses are correctly set in all scripts before running.
- To test the connection:
  1. On the FLOWER, run: `flower_server.py`
  2. On the PATT, run: `patt_client.py`

If the connection is successful, messages sent from the PATT should be received on the FLOWER. If not, check and update the IP addresses in both scripts.

---

## 🔹 Script Directory Structure

- **`ON_PATT_controlling_FLOWER/`**  
  Contains scripts that run on the PATT and send commands/data to the FLOWER.

- **`ON_FLOWER_receiving_from_PATT/`**  
  Contains scripts that run on the FLOWER and receive commands/data from the PATT.  
  These scripts save results to `.json` files for later analysis.

---

## 🔹 Scan Script Pairs

Each PATT script has a corresponding FLOWER script. Always start the FLOWER-side script first.

---

### 1. **SNR Calibration Scans**

**Used to generate SNR slope from peak-to-peak signal measurements.**

- `patt_attenuation_scan_flower.py`  
  → `find_SNR_from_p2p.py`  
  → `find_SNR_from_p2p_phased.py` (for phased mode)

**Output analysis:**  
Data saved to JSON files is analyzed with:  
`NuDelay/Shams_analyzing_scripts/(HI-Lo or phased)/get_SNR_from_p2p.py`

**Purpose:**  
This should be run prior to efficiency scans to calculate the SNR slope.

---

### 2. **Single-Angle Efficiency Scans**

**Performs a scan at a fixed angle to measure trigger efficiency vs attenuation.**

- `patt_attenuation_scan_flower.py`  
  → `coincidence_scan_over_attenuations_for_single_efficiency.py`  
  → `coincidence_scan_over_attenuations_for_single_efficiency_phased.py` (for phased mode)

**Output analysis:**  
`NuDelay/Shams_analyzing_scripts/(HI-Lo or phased)/efficiency_vs_predicted_SNR_sigmoid.py`

**Note:**  
The angle setting is defined in `NuDelay/PATT_calibration_setup_scripts`.

---

### 3. **Full-Angle Scans**

**Performs scans across a range of angles and attenuations. Can be run overnight.**

#### Hi-Lo Mode
- `patt_angle_and_attenuation_scan.py`  
  → `coincidence_scan_angles_and_attenuations.py`

- `patt_angle_and_attenuation_scan_custom_delays.py`  
  → `coincidence_scan_angles_and_attenuations.py`  
  _(Uses custom delay list)_

#### Phased Mode
- `patt_angle_and_attenuation_scan_phased_mode.py`  
  → `coincidence_scan_angles_and_attenuations_phased.py`

- `patt_angle_and_attenuation_scan_phased_custom_delays.py`  
  → `coincidence_scan_angles_and_attenuations_phased.py`  
  _(Uses custom delay list)_

**Output analysis:**  
`NuDelay/Shams_analyzing_scripts/(HI-Lo or phased)/full_angle_scan_analyzer.py`

**Custom Delay Note:**  
Custom versions require a JSON file with a time delay list.  
Delays can be based on ice models using NuRadioMC.

**Delay Generator Script:**  
`NuDelay/Shams_analyzing_scripts/custom_time_delay_list_maker.py`

---

## 🔹 Tips

- Always run the FLOWER-side scripts before starting the corresponding PATT-side scripts.
- Ensure all IP addresses are updated and match the local network setup.
- For long scans, consider running them overnight.

