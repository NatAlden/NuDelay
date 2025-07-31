Operating guide and scripts for the P.A.T.T (Phased Array Trigger Tester)

Operating guidelines/general info:
1. Need a power supply with 12V and 5V output (max 1A current for both outputs)
2. Do not start 12V power supply with pulsers plugged in (the current goes too high). Instead,
start with the pulsers unplugged and then plug in
3. 100 kHz seems to work well as a trigger rate, could go lower or a bit higher as necessary
4. The pulsers are Highland Technologies J240 models
5. The digital delay generator (DDG) is a Highland Technologies model T660
6. The system is controlled by a BeagleBone Black (BBB) communicating over i2c to the attenuator board and over serial to the DDG

Script information:
1. If trigger and power are both on but no pulses are visible, run start_triggering.py
2. Use atten_i2c [atten_value] to set the attenuation: atten_value ranges from 0 (0 dB) to 127 (31.75 dB) in steps of 0.25 dB

##################
Important Scripts
##################

# PATT Scripts Overview

This repository contains scripts for operating the Phased Array Trigger Tester (PATT), including time delay configuration and signal attenuation control. Below is a breakdown of the most important scripts and their functions.

---

## 🔹 General Startup

**`start_triggering.py`**  
Use this script to confirm the basic functionality of the PATT after setup. It helps verify that triggering and signal generation are working. As an alternative, you can run one of the delay scripts and one of the attenuation scripts.

---

## Time Delay Control Scripts

**1. `time_calibration_from_presets.py`**  
- Loads delay presets from `delay_presets.json`.  
- Allows you to apply an existing preset or create and modify new ones.  
- Useful for calibration and for visualizing delays on an oscilloscope or via the FLOWER system.  
- All delays are in nanoseconds (ns).

**2. `set_pulse_angle.py`**  
- Requires zero-point calibration (where all pulses are aligned).  
- Accepts an angle (in degrees) and applies delays using a plane-wave assumption in ice (index of refraction = 1.78).  
- 0° corresponds to no delay (horizontal arrival).

**3. `set_pulse_angle_cable_delays.py`**  
- Same as `set_pulse_angle.py` but includes an additional delay term to account for cable-specific delays.  
- Recommended for beam testing with `flower-status`.

**Available Beam Angles:**  
`[-60.0, -45.12, -33.44, -23.18, -13.66, -4.52, 4.52, 13.66, 23.18, 33.44, 45.12, 60.0]`

---

## Attenuation Control Scripts

**1. `calibrate_test_attenuations_per_channel.py`**  
- Uses `atten_presets.json` for attenuation presets.  
- Prompts user to choose an existing preset or create a new one by typing `"new"`.  
- Applies the attenuation settings directly to each channel (DAC scale: 0 to 127).

**2. `percent_attenuation_control.py`**  
- Prompts the user to input a percentage from 0 to 100.  
- Applies uniform attenuation across all channels based on that percentage.  
  - `100%` = fully open (maximum voltage)  
  - `0%` = fully attenuated (DAC value = 127)

---

## Notes

- All scripts are meant to be run on the BeagleBone connected to the PATT.
- Make sure the BeagleBone is powered and connected before running scripts.
- Be cautious when changing attenuation during scans; use `sleep()` to avoid transient unattenuated pulses.

