# PATT Data Analysis & Visualization Scripts

This set of scripts is used for analyzing and visualizing data from PATT–FLOWER scans. It includes tools for:

- Signal-to-noise ratio (SNR) extraction
- Efficiency plotting
- Full scan visualization
- Spectral analysis and event plotting
- Custom delay generation using NuRadioMC
- Cross-comparison of multiple scan results

Hi-Lo and Phased Array analyses are handled in separate folders to maintain clarity and accuracy.

---

## 🔹 Main Analysis Scripts

Located in:  
`NuDelay/Shams_analyzing_scripts/(HI-Lo or phased)/`

### 1. `get_SNR_from_p2p.py`

- Inputs a JSON file from an attenuation scan.
- Computes the relationship (slope) between attenuation setting and measured SNR.
- Requires the RMS noise level of the 4 channels, which can be obtained by:

  - Running the `utils.py` script in:  
    `NuDelay/ON_FLOWER_receiving_from_PATT/`
  - Enable the `noise_rms()` function.
  - Ensure the waveform used is only noise:  
    - Either turn off the function generator  
    - Or set the PATT attenuation to **0%**

- Outputs:
  - SNR slope (attenuation → SNR)
  - Diagnostic plot (save paths and filenames are configurable in the script)

---

### 2. `efficiency_vs_predicted_SNR_sigmoid.py`

- Analyzes a single attenuation scan at one fixed delay setting.
- Plots efficiency (pass rate) vs predicted SNR.
- Useful for generating sigmoid efficiency curves.

---

### 3. `full_angle_scan_analyzer.py`

- Analyzes full scans over multiple angles and attenuations.
- Inputs the JSON output from the FLOWER-side scan script.
- Produces:
  - A plot of 50% pass-rate SNR vs angle.
  - (Phased mode only) Overlays beamforming lines.

- At the end of the script:
  - You can choose to save the resulting plot data in a JSON format.
  - These files can be used in **combined analysis** comparisons.

---

## 🔹 Combined Analysis

Located in:  
`NuDelay/Shams_analyzing_scripts/combined_analysis/`

### `analysis_plotter.py`

- Loads the JSON outputs saved by `full_angle_scan_analyzer.py`
- Plots multiple curves on the same plot for comparison.

---

## 🔹 Custom Delay List Generator

Located in:  
`NuDelay/Shams_analyzing_scripts/custom_time_delay_list_maker/`

### `delay_list_v2.py`

- Uses **NuRadioMC** to calculate time delays to each antenna channel from a simulated pulser drop.
- Geometry of the drop (depth, lateral distance, etc.) is user-configurable.
- Outputs:
  - A JSON file containing angles and time delays.

- Use these delay lists as input to the custom scan scripts in:  
  `NuDelay/ON_PATT_controlling_FLOWER/`

---

## 🔹 Notes

- Always match the analysis script to the corresponding scan mode (Hi-Lo or Phased).
- All outputs (SNR slopes, plots, comparison data) are saved in the working directory or specified output paths.
- JSON filenames and save paths must be updated manually in each script.

