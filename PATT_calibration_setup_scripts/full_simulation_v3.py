import smbus
import serial
import numpy as np
import time

# === Constants ===
A = 91.916  # from exponential fit
k = 0.026
SWEEP_NS = 3
DURATION = 2  # seconds per channel sweep
STEPS = 100
STEP_DELAY = DURATION / (2 * STEPS)

# === Channel mappings ===
i2c_addresses = {'C4': 0x38, 'C2': 0x3c, 'C1': 0x3e}

# ✅ Corrected delay mapping
delay_cmds = {'C4': 'BD', 'C1': 'CD', 'C2': 'DD'}

# Origin delays in nanoseconds
origins = {'C1': 0.6, 'C2': 2.03, 'C4': 0.1}

# === I2C Setup ===
bus = smbus.SMBus(2)
output_reg = 0x01
config_reg = 0x03

def setAttenuation(addr, atten_value):
    atten_value = int(round(atten_value))
    bits = '{:07b}'.format(atten_value)
    mapped = "0" + bits[0:3] + bits[7:2:-1]
    val = int(mapped, 2)
    bus.write_byte_data(addr, output_reg, val)

def setupAttenuator(addr):
    bus.write_byte_data(addr, output_reg, 0x00)
    bus.write_byte_data(addr, config_reg, 0x00)
    current = bus.read_byte_data(addr, output_reg)
    bus.write_byte_data(addr, output_reg, current | 0x02)

def percent_to_attenuation(p):
    if p >= 100: return 0
    if p <= 0: return 127
    return int(round(np.clip(-np.log(p / A) / k, 0, 127)))

# === Serial Setup for T660 ===
ser = serial.Serial(port="/dev/ttyUSB0", baudrate=38400, timeout=1,
                    stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
ser.close()
ser.open()

def send_command(cmd, loud=False):
    ser.write(str.encode(cmd + '\n'))
    line = ser.readline().decode().strip()
    if loud:
        print(f"> {cmd} => {line}")
    return line

def init_delay_system():
    send_command("TRIGGER POS")
    send_command("DW 2u")
    for cmd in ['ASET', 'BSET', 'CSET', 'DSET']:
        send_command(cmd)
    reset_all_delays()

def set_delay(ch_label, value_ns):
    cmd = delay_cmds.get(ch_label)
    if cmd:
        send_command(f"{cmd} {value_ns:.3f}n")

def reset_all_delays():
    for ch in origins:
        set_delay(ch, origins[ch])
    time.sleep(0.5)

# === Animation per Channel ===
def animate_channel(channel_label):
    print(f"\n🎬 Animating channel {channel_label}...")

    addr = i2c_addresses[channel_label]
    delay_cmd = delay_cmds[channel_label]
    origin = origins[channel_label]

    setupAttenuator(addr)

    # Set other channels to 0 dB (max amplitude)
    for other_label in i2c_addresses:
        if other_label != channel_label:
            setupAttenuator(i2c_addresses[other_label])
            setAttenuation(i2c_addresses[other_label], 0)

    # Sweep forward
    for i in range(STEPS + 1):
        delta = SWEEP_NS * i / STEPS
        delay_val = origin + delta
        percent = max(0, 100 - (i * 100 / STEPS))
        atten_val = percent_to_attenuation(percent)

        send_command(f"{delay_cmd} {delay_val:.3f}n")
        setAttenuation(addr, atten_val)
        time.sleep(STEP_DELAY)

    # Sweep back
    for i in range(STEPS + 1):
        delta = SWEEP_NS - (SWEEP_NS * i / STEPS)
        delay_val = origin + delta
        percent = max(0, i * 100 / STEPS)
        atten_val = percent_to_attenuation(percent)

        send_command(f"{delay_cmd} {delay_val:.3f}n")
        setAttenuation(addr, atten_val)
        time.sleep(STEP_DELAY)

    print(f"✅ Finished animation for {channel_label}")

# === Main ===
def main():
    print("🔧 Initializing systems...")
    if not ser.isOpen():
        print("❌ Serial port not open.")
        return

    init_delay_system()

    for ch_label in ['C2', 'C1', 'C4']:
        animate_channel(ch_label)
        time.sleep(0.5)

    print("\n✅ All channel animations complete.")

if __name__ == "__main__":
    main()

