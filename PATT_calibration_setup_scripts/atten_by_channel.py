import smbus

# Initialize I2C bus 2 (for BeagleBone Black)
bus = smbus.SMBus(2)

# Register addresses
output_reg = 0x01
config_reg = 0x03

# I2C addresses for 4 channels
CHANNEL_ADDRESSES = [0x38, 0x3a, 0x3c, 0x3e]

# Preset attenuation options (attenuation values in dB)
# Preset attenuation options (attenuation values in dB)
attenuation_presets = {
    "flat_0dB": [0, 0, 0, 0],
    "mild_4dB": [16, 16, 16, 16],
    "ramp": [0, 16, 32, 48],
    "custom_1": [4, 24, 12, 40],
    "custom_2": [8, 8, 8, 64],
    "0_out": [70, 0, 0, 0],
    "1_out": [0, 70, 0, 0],
    "2_out": [0, 0, 70, 0],
    "3_out": [0, 0, 0, 50],
    "3_out_2": [0, 0, 0, 63],
    "3_out_3": [0, 0, 0, 64],
    "3_out_4": [0, 0, 0, 65],
    "3_out_5": [0, 0, 0, 66],
}
    


def write(i2c_address, register, cmd):
    return bus.write_byte_data(i2c_address, register, cmd)

def read(i2c_address, register):
    return bus.read_byte_data(i2c_address, register)

def setup(address):
    write(address, output_reg, 0x00)
    write(address, config_reg, 0x00)

def getOutputRegisterValue(address):
    return read(address, output_reg)

def setOutput(address):
    ret = getOutputRegisterValue(address)
    write(address, output_reg, ret | 0x02)

def setAttenuation(address, atten_value=0):
    atten_bits_value = '{:07b}'.format(atten_value)
    mapped_atten_bits = "0" + atten_bits_value[0:3] + atten_bits_value[7:2:-1]
    new_reg_value = int(mapped_atten_bits, 2)
    write(address, output_reg, new_reg_value)

def set_individual_attens(atten_values):
    for address, value in zip(CHANNEL_ADDRESSES, atten_values):
        setup(address)
        setOutput(address)
        setAttenuation(address, value)

def main():
    print("Available attenuation presets:\n")
    for i, key in enumerate(attenuation_presets):
        print(f"{i}: {key} => {attenuation_presets[key]}")

    choice = input("\nEnter the number of the preset you want to apply: ")

    try:
        preset_key = list(attenuation_presets.keys())[int(choice)]
        selected_values = attenuation_presets[preset_key]
        print(f"\nApplying preset '{preset_key}' with values {selected_values}")
        set_individual_attens(selected_values)
        print("Done.")
    except (ValueError, IndexError):
        print("Invalid selection. Please run the program again and choose a valid number.")

if __name__ == "__main__":
    main()

