import smbus
import numpy as np
import time

# I2C setup
bus = smbus.SMBus(2)
output_reg = 0x01
config_reg = 0x03

# Use only working channels
CHANNEL_INDEXES = [0, 2, 3]
CHANNEL_ADDRESSES = [0x38, 0x3c, 0x3e]

# Fit constants from your exponential curve
A = 91.916
k = 0.026

def write(i2c_address, register, cmd):
    bus.write_byte_data(i2c_address, register, cmd)

def read(i2c_address, register):
    return bus.read_byte_data(i2c_address, register)

def setup(address):
    write(address, output_reg, 0x00)
    write(address, config_reg, 0x00)

def getOutputRegisterValue(address):
    return read(address, output_reg)

def setOutput(address):
    val = getOutputRegisterValue(address)
    write(address, output_reg, val | 0x02)

def setAttenuation(address, atten_value=0):
    atten_value = int(round(atten_value))
    atten_bits = '{:07b}'.format(atten_value)
    mapped = "0" + atten_bits[0:3] + atten_bits[7:2:-1]
    value = int(mapped, 2)
    write(address, output_reg, value)

def percent_to_attenuation(p):
    if p >= 100:
        return 0
    if p <= 0:
        return 127
    try:
        x = -np.log(p / A) / k
        return int(round(np.clip(x, 0, 127)))
    except:
        return 127

def apply_attenuation_all_channels(atten_value):
    for i, ch in enumerate(CHANNEL_INDEXES):
        addr = CHANNEL_ADDRESSES[i]
        setup(addr)
        setOutput(addr)
        setAttenuation(addr, atten_value)

def animated_sweep():
    steps = list(range(100, -1, -1)) + list(range(0, 101, 1))  # 100→0, then 0→100
    delay_per_step = 2 / len(steps)  # evenly space over 2 seconds

    print("🎞️ Starting attenuation sweep (100% → 0% → 100%) over 2 seconds...")
    for percent in steps:
        atten = percent_to_attenuation(percent)
        apply_attenuation_all_channels(atten)
        time.sleep(delay_per_step)

    print("✅ Sweep complete.")

# --- Run Sweep ---
if __name__ == "__main__":
    animated_sweep()

