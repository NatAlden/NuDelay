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
