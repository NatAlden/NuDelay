import smbus
import numpy as np

# I2C bus for BeagleBone Black
bus = smbus.SMBus(2)

# Register addresses
output_reg = 0x01
config_reg = 0x03

# I2C addresses for working channels: A, C, D
CHANNEL_INDEXES = [0, 2, 3]
CHANNEL_ADDRESSES = [0x38, 0x3c, 0x3e]

# Reference calibration table (used for linear regression only)
calibration_table = {
    100: [0, 0, 0, 1],
    75:  [9, 10, 9, 9],
    50:  [24, 20, 24, 24],
    25:  [49, 40, 48, 48],
}

# --- Hardware Communication Functions --- #
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
    current_val = getOutputRegisterValue(address)
    write(address, output_reg, current_val | 0x02)

def setAttenuation(address, atten_value=0):
    atten_bits = '{:07b}'.format(atten_value)
    mapped_bits = "0" + atten_bits[0:3] + atten_bits[7:2:-1]
    new_reg_value = int(mapped_bits, 2)
    write(address, output_reg, new_reg_value)

# --- Prediction Logic (Linear Regression per Channel) --- #
def predict_all_channels(signal_percent):
    """
    Predicts attenuation values for all 4 channels using linear regression.
    Ignores channel 1 (index 1), returns None there.
    """
    percentages = list(calibration_table.keys())
    predicted_attens = []

    for ch in range(4):
        if ch == 1:
            predicted_attens.append(None)
            continue

        y = [calibration_table[p][ch] for p in percentages]
        x = percentages
        m, b = np.polyfit(x, y, deg=1)
        atten_val = m * signal_percent + b
        predicted_attens.append(int(round(atten_val)))

    return predicted_attens

def apply_attenuations(percent):
    all_attens = predict_all_channels(percent)
    print(f"\nInterpolated attenuation values for {percent}% signal:")
    for ch in range(4):
        status = "(used)" if ch in CHANNEL_INDEXES else "(ignored)"
        print(f"  Channel {ch}: {all_attens[ch]} {status}")

    for i, ch in enumerate(CHANNEL_INDEXES):
        addr = CHANNEL_ADDRESSES[i]
        atten_val = all_attens[ch]
        setup(addr)
        setOutput(addr)
        setAttenuation(addr, atten_val)

    print("✅ Attenuation applied to working channels.\n")

# --- Main Loop --- #
def main():
    try:
        percent = float(input("Enter desired signal strength (0–100%): "))
        if not (0 <= percent <= 100):
            raise ValueError
        apply_attenuations(percent)
    except ValueError:
        print("❌ Invalid input. Please enter a number between 0 and 100.")

if __name__ == "__main__":
    main()

