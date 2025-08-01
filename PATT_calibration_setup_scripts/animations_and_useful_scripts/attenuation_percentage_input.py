
import smbus
import numpy as np

# I2C setup
bus = smbus.SMBus(2)
output_reg = 0x01
config_reg = 0x03

# Only use channels A, C, D
CHANNEL_INDEXES = [0, 1, 2, 3]
CHANNEL_ADDRESSES = [0x3e, 0x3c, 0x3a, 0x38]
CHANNEL_LABELS = ['A', 'B', 'C', 'D']


# Fit parameters from your exponential model
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

# --- Calculate attenuation value from percentage
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

def apply_percentage(percent):
    attenuation = percent_to_attenuation(percent)
    print(f"\nTarget %: {percent} → Attenuation value: {attenuation}")

    for i, ch in enumerate(CHANNEL_INDEXES):
        addr = CHANNEL_ADDRESSES[i]
        setup(addr)
        setOutput(addr)
        setAttenuation(addr, attenuation)

    print("✅ Attenuation applied to channels A B, C, D.")

# --- Main ---
def main():
    try:
        percent = float(input("Enter desired signal strength (0–100%): "))
        if not (0 < percent <= 100):
            raise ValueError
        apply_percentage(percent)
    except ValueError:
        print("❌ Please enter a valid percentage between 1 and 100.")

if __name__ == "__main__":
    main()

