# NuDelay

# PATT Project: Comprehensive README

Welcome to the documentation for the **Phased Array Trigger Tester (PATT)** project. This guide outlines the structure, setup, and operation of the full PATT/FLOWER experimental system used for testing trigger efficiency and waveform behavior in a controlled lab environment. It aims to provide a step-by-step reference for operating the system, running scans, and analyzing the data.

---

## Table of Contents

1. [Overview](#overview)
2. [PATT System Overview](#patt-system-overview)
3. [Initial Setup and Power-Up](#initial-setup-and-power-up)
4. [Connecting to FLOWER](#connecting-to-flower)
5. [Trigger Modes: Hi-Lo and Phased](#trigger-modes-hi-lo-and-phased)
6. [Running Delay and Attenuation Scripts](#running-delay-and-attenuation-scripts)
7. [Running PATT/FLOWER Scans](#running-pattflower-scans)
8. [Data Analysis and Visualization](#data-analysis-and-visualization)
9. [Custom Delay Generation](#custom-delay-generation)
10. [Troubleshooting & Tips](#troubleshooting--tips)

---

## Overview

The PATT project is designed to simulate particle event triggers in a lab by generating fast pulses, delaying and attenuating them as needed, and evaluating trigger performance using a separate receiver unit known as FLOWER. It supports both Hi-Lo and phased array trigger modes and is highly customizable.

---

## PATT System Overview

The PATT consists of:

* A **BeagleBone board** for script control
* 4 **Highland Technologies J240-1 fast pulsers**
* 1 **T660-1 delay/pulse generator**
* 1 **Custom attenuation board**
* 1 **RS-232 interface board**
* 1 **Power distribution block**
* Various filters, cabling, and a chassis

External components:

* A **12V power supply** (draws \~0.9 A)
* A **function generator** for timing signal generation

See the detailed [PATT Hardware Documentation](./https://docs.google.com/document/d/1k0xs5KYfx7s5R0da7UKOwDlfDsW09W0x/edit?usp=sharing&ouid=101918658015293007442&rtpof=true&sd=true) for power-up steps and safety notes.

---

## Initial Setup and Power-Up

1. **Verify hardware connections.** Make sure the RS-232, pulse, delay, and attenuation lines are properly wired.
2. **Power the system in sequence:**

   * Connect 12V power to the power block.
   * Power on the BeagleBone.
   * Connect the pulsers **one-by-one** (watch for current draw increases).
3. **Set up filters** inline before output.
4. **Connect the BeagleBone via Ethernet** to your control machine.
5. **Test device communication** by pinging the BeagleBone and opening an SSH session.

---

## Connecting to FLOWER

The FLOWER unit is a DAQ system that receives pulse triggers from the PATT.

To establish communication:

1. Connect both PATT and FLOWER to the same network.
2. Set correct IP addresses in the scripts.
3. On the FLOWER: Run `flower_server.py`
4. On the PATT: Run `patt_client.py`
5. If connection fails, check the network and IP configuration.

See [PATT–FLOWER Scan Communication README](./PATT_FLOWER_Scans.md) for detailed instructions.

---

## Trigger Modes: Hi-Lo and Phased

You can select the desired trigger mode by configuring delay and attenuation scripts on the PATT.

* **Hi-Lo Trigger**: Sets a delay pattern simulating simple vertical pulses.
* **Phased Trigger**: Uses beamforming-style delays to mimic incoming angles.

Use scripts such as:

* `set_pulse_angle.py`
* `set_pulse_angle_cable_delays.py`
* `time_calibration_from_presets.py`

Set up corresponding filters and save delay presets for reproducibility.

---

## Running Delay and Attenuation Scripts

Use the following to calibrate or control pulse parameters:

* Delay:

  * `time_calibration_from_presets.py`
  * `set_pulse_angle.py`
  * `set_pulse_angle_cable_delays.py`

* Attenuation:

  * `calibrate_test_attenuations_per_channel.py`
  * `percent_attenuation_control.py`

All scripts are located in `NuDelay/PATT_calibration_setup_scripts/`. See [Delay & Attenuation Scripts README](./Delay_Attenuation_Scripts.md).

---

## Running PATT/FLOWER Scans

Scans involve two paired scripts:

* **ON\_PATT\_controlling\_FLOWER/** — sender
* **ON\_FLOWER\_receiving\_from\_PATT/** — receiver

### Common Pairings:

* **SNR Calibration**

  * `patt_attenuation_scan_flower.py` → `find_SNR_from_p2p.py`

* **Single-Angle Scans**

  * `patt_attenuation_scan_flower.py` → `coincidence_scan_over_attenuations_for_single_efficiency.py`

* **Full-Angle Scans**

  * `patt_angle_and_attenuation_scan.py` → `coincidence_scan_angles_and_attenuations.py`
  * Optional custom delay versions available

See [Scan Scripts README](./Scan_Scripts_README.md) for a full list and instructions.

---

## Data Analysis and Visualization

Scripts in `NuDelay/Shams_analyzing_scripts/` provide:

* **SNR slope generation**: `get_SNR_from_p2p.py`
* **Efficiency curves**: `efficiency_vs_predicted_SNR_sigmoid.py`
* **Full-scan plotting**: `full_angle_scan_analyzer.py`
* **Multi-scan comparison**: `combined_analysis/analysis_plotter.py`

RMS noise levels must be calculated with `utils.py` using noise-only traces.

Refer to [Analysis README](./Analysis_README.md) for usage examples.

---

## Custom Delay Generation

Located in: `NuDelay/Shams_analyzing_scripts/custom_time_delay_list_maker/`

Script: `delay_list_v2.py`

* Uses NuRadioMC to calculate realistic delays for a pulser drop
* Saves angle–delay pairs to a JSON file
* Can be used in custom scan scripts under `ON_PATT_controlling_FLOWER/`

---

## Troubleshooting & Tips

* Always run FLOWER-side scripts **before** PATT-side.
* Confirm IP address consistency across all devices.
* Use `sleep()` delays after changing attenuation or delays to avoid race conditions.
* Keep backup JSONs of successful scan configurations.
* Logs and plots are stored locally — organize by timestamp for reproducibility.

---

For any issues or contributions, please reach out to the maintainer or submit a pull request.

---

