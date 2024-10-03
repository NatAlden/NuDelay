import smbus
import numpy as np

# I2C setup
bus = smbus.SMBus(2)
output_reg = 0x01
config_reg = 0x03

# Channel mappings
CHANNEL_INDEXES = [0, 1, 2, 3]
CHANNEL_ADDRESSES = [0x3e, 0x3c, 0x3a, 0x38]
CHANNEL_LABELS = ['A', 'B', 'C', 'D']

# Fit parameters from exponential model
A = 91.916
k = 0.026

# --- I2C functions
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

# --- Reverse model: attenuation to percentage
def attenuation_to_percent(atten_value):
    try:
        return 100 * 10 ** (-atten_value /80)
    except:
        return 0.0

# --- Main function to apply attenuation and report %
def apply_attenuation_to_all_channels(atten_value):
    percent = attenuation_to_percent(atten_value)
    print(f"Applying attenuation value = {atten_value} → Estimated signal strength = {percent:.2f}%")

    for i in CHANNEL_INDEXES:
        addr = CHANNEL_ADDRESSES[i]
        setup(addr)
        setOutput(addr)
        setAttenuation(addr, atten_value)

    return percent

# If run directly
if __name__ == "__main__":
    try:
        atten_value = int(input("Enter attenuation value (0–127): "))
        if not (0 <= atten_value <= 127):
            raise ValueError
        apply_attenuation_to_all_channels(atten_value)
    except ValueError:
        print("Invalid input. Please enter an integer between 0 and 127.")
