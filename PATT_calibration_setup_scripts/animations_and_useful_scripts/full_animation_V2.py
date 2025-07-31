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

# === Full 4-channel mapping ===
CHANNEL_LABELS = ['A', 'B', 'C', 'D']
CHANNEL_ADDRESSES = [0x3e, 0x3c, 0x3a, 0x38]  # A, B, C, D

# Delay commands per channel
delay_cmds = {'A': 'AD', 'B': 'BD', 'C': 'CD', 'D': 'DD'}

# Origin delay times in nanoseconds for calibration
origins = {'A': 4.18, 'B': 4.19, 'C': 2.00, 'D': 1.36}

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
    for ch in CHANNEL_LABELS:
        set_delay(ch, origins[ch])
    time.sleep(0.5)

# === Animation per Channel ===
def animate_channel(index):
    ch_label = CHANNEL_LABELS[index]
    addr = CHANNEL_ADDRESSES[index]
    origin = origins[ch_label]
    delay_cmd = delay_cmds[ch_label]

    print(f"\n🎬 Animating channel {ch_label}...")

    setupAttenuator(addr)

    # Set other channels to max amplitude (0 dB)
    for i, other_label in enumerate(CHANNEL_LABELS):
        if i != index:
            setupAttenuator(CHANNEL_ADDRESSES[i])
            setAttenuation(CHANNEL_ADDRESSES[i], 0)

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

    print(f"✅ Finished animation for channel {ch_label}")

# === Main ===
def main():
    print("🔧 Initializing system...")
    if not ser.isOpen():
        print("❌ Serial port not open.")
        return

    init_delay_system()

    for index in range(4):
        animate_channel(index)
        time.sleep(0.5)

    print("\n✅ All channel animations complete.")

if __name__ == "__main__":
    main()

