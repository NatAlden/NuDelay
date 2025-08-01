import smbus
import json
import os

PRESET_FILE = "atten_presets.json"

# I2C setup
bus = smbus.SMBus(2)
output_reg = 0x01
config_reg = 0x03

# All 4 channels now work and are mapped 1:1
#CHANNEL_ADDRESSES = [0x38, 0x3a, 0x3c, 0x3e]
CHANNEL_ADDRESSES = [0x3e, 0x3c, 0x3a, 0x38]
CHANNEL_LABELS = ['A', 'B', 'C', 'D']

# ---- I2C Communication ----
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

# ---- Preset Management ----
def load_presets():
    if os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, 'r') as f:
            return json.load(f)
    else:
        return {
            "default": [0, 0, 0, 0]
        }

def save_presets(presets):
    with open(PRESET_FILE, 'w') as f:
        json.dump(presets, f, indent=2)

def prompt_new_preset():
    print("Enter new attenuation values (integers) for channels A, B, C, D (in 0.5 dB units).")
    values = []
    for label in CHANNEL_LABELS:
        while True:
            try:
                val = int(input(f"  {label}: "))
                values.append(val)
                break
            except ValueError:
                print("    Must be an integer.")
    return values

# ---- Application ----
def apply_attenuations(values):
    print("\nApplying attenuation values:")
    for i, val in enumerate(values):
        print(f"  Channel {CHANNEL_LABELS[i]} (addr {hex(CHANNEL_ADDRESSES[i])}): {val} (0.5 dB steps)")

        addr = CHANNEL_ADDRESSES[i]
        setup(addr)
        setOutput(addr)
        setAttenuation(addr, val)

    print("✅ Attenuation applied.\n")

# ---- Main ----
def main():
    presets = load_presets()
    names = list(presets.keys())

    print("\nAvailable attenuation presets:")
    for i, name in enumerate(names):
        print(f"  [{i}] {name}: {presets[name]}")

    choice = input("\nSelect preset number or type 'new' to create one: ").strip()

    if choice.lower() == 'new':
        name = input("Enter a name for this preset: ").strip()
        new_vals = prompt_new_preset()
        presets[name] = new_vals
        save_presets(presets)
        apply_attenuations(new_vals)
    elif choice.isdigit() and int(choice) < len(names):
        selected_name = names[int(choice)]
        apply_attenuations(presets[selected_name])
    else:
        print("❌ Invalid input. Please try again.")

if __name__ == "__main__":
    main()

