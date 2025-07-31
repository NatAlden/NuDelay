import serial
import time
import json
import os

PRESETS_FILE = "delay_presets.json"

def load_presets():
    if os.path.exists(PRESETS_FILE):
        with open(PRESETS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {
            "original": {"A": "1n", "B": "0n", "C": "0n", "D": "0n"}
        }

def save_presets(presets):
    with open(PRESETS_FILE, 'w') as f:
        json.dump(presets, f, indent=2)

def send_command(ser, command, loud=True):
    ser.write((command + '\n').encode())
    line = ser.readline()
    if loud:
        print(str(line.decode().strip()))

def apply_delay_preset(ser, delays):
    for ch, delay in delays.items():
        send_command(ser, f"{ch}D {delay}")
    send_command(ser, 'DW 2u')   # Set pulse width
    send_command(ser, 'DSET')
    for ch in delays:
        send_command(ser, f"{ch}SET")

def prompt_new_preset():
    print("\nCreate new preset:")
    delays = {}
    for ch in ['A', 'B', 'C', 'D']:
        delays[ch] = input(f"Enter delay for channel {ch} (e.g. 3n, 5u): ").strip()
    return delays

def main():
    presets = load_presets()
    preset_names = list(presets.keys())

    ser = serial.Serial(
        port="/dev/ttyUSB0",
        baudrate=38400,
        timeout=1,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    ser.close()
    ser.open()

    if not ser.isOpen():
        print("Failed to open serial port.")
        return

    print("\nAvailable Presets:")
    for i, name in enumerate(preset_names):
        print(f" [{i}] {name}: {presets[name]}")

    choice = input("\nChoose preset number or type 'new' to create one: ").strip()

    if choice == 'new':
        name = input("Name for the new preset: ").strip()
        new_preset = prompt_new_preset()
        presets[name] = new_preset
        save_presets(presets)
        apply_delay_preset(ser, new_preset)
    elif choice.isdigit() and int(choice) < len(preset_names):
        selected = preset_names[int(choice)]
        apply_delay_preset(ser, presets[selected])
        print(f"Applied preset: {selected}")
    else:
        print("Invalid choice.")

    ser.close()
    print("Done.")

if __name__ == "__main__":
    main()

