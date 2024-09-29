import smbus
import numpy as np

# I2C setup
bus = smbus.SMBus(2)
output_reg = 0x01
config_reg = 0x03

# Channel info
CHANNEL_INDEXES = [0, 1, 2, 3]
CHANNEL_ADDRESSES = [0x3e, 0x3c, 0x3a, 0x38]
CHANNEL_LABELS = ['A', 'B', 'C', 'D']

# --- I2C functions ---
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

# --- Logarithmic model ---
def percent_to_attenuation(p):
    """
    Converts signal strength percentage to attenuation value (0–127 scale)
    using the inverse of 100 * 10^(-atten/80)
    """
    if p >= 100:
        return 0
    if p <= 0:
        return 127
    try:
        attenuation = -80 * np.log10(p / 100)
        return int(round(np.clip(attenuation, 0, 127)))
    except:
        return 127

# --- Apply attenuation ---
def apply_percentage(percent):
    attenuation = percent_to_attenuation(percent)
    print(f"\nTarget %: {percent:.2f} → Attenuation value: {attenuation}")

    for i in CHANNEL_INDEXES:
        addr = CHANNEL_ADDRESSES[i]
        setup(addr)
        setOutput(addr)
        setAttenuation(addr, attenuation)

    print("✅ Attenuation applied to channels A, B, C, D.")

# --- Main ---
def main():
    try:
        percent = float(input("Enter desired signal strength (0–100%): "))
        if not (0 <= percent <= 100):
            raise ValueError
        apply_percentage(percent)
    except ValueError:
        print(" Please enter a valid percentage between 0 and 100.")

if __name__ == "__main__":
    main()

