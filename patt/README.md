Operating guide and scripts for the P.A.T.T (Phased Array Trigger Tester)

Operating guidelines:
1. Need a power supply with 12V and 5V output (max 1A current for both outputs)
2. Do not start 12V power supply with pulsers plugged in (the current goes too high). Instead,
start with the pulsers unplugged and then plug in
3. 100 kHz seems to work well as a trigger rate, could go lower or a bit higher as necessary

Script information:
1. If trigger and power are both on but no pulses are visible, run start_triggering.py
2. Use atten_i2c [atten_value] to set the attenuation. atten_value ranges from 0 (0 dB) to 127 (31.75 dB) in steps of 0.25 dB
