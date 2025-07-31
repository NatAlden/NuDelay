import smbus
import serial
import numpy as np
import time

# --- Attenuation Control Setup (I2C via smbus) ---
bus = smbus.SMBus(2)
output_reg = 0x01
config_reg = 0x03
CHANNEL_INDEXES = [0, 2, 3]
CHANNEL_ADDRESSES = [0x38, 0x3c, 0x3e]

# Attenuation exponential model (from your fit)
A = 91.916
k = 0.026

def setAttenuation(addr, atten_value):
    atten_value = int(round(atten_value))
    atten_bits = '{:07b}'.format(atten_value)
    mapped = "0" + atten_bits[0:3] + atten_bits[7:2:-1]
    value = int(mapped, 2)
    bus.write_byte_data(addr, output_reg, value)

def setupAttenuator(addr):
    bus.write_byte_data(addr, output_reg, 0x00)
    bus.write_byte_data(addr, config_reg, 0x00)
    curr = bus.read_byte_data(addr, output_reg)
    bus.write_byte_data(addr, output_reg, curr | 0x02)

def percent_to_attenuation(p):
    if p >= 100: return 0
    if p <= 0: return 127
    return int(round(np.clip(-np.log(p / A) / k, 0, 127)))

def animate_attenuation():
    print("🎞️ Animating attenuation (100% → 0% → 100%)...")
    steps = list(range(100, -1, -1)) + list(range(0, 101, 1))
    delay_per_step = 2 / len(steps)

    for p in steps:
        atten = percent_to_attenuation(p)
        for i, ch in enumerate(CHANNEL_INDEXES):
            setupAttenuator(CHANNEL_ADDRESSES[i])
            setAttenuation(CHANNEL_ADDRESSES[i], atten)
        time.sleep(delay_per_step)
    print("✅ Attenuation animation complete.\n")

# --- Delay Control Setup (Serial to T660) ---
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

origins = {'A': 0.0, 'B': 0.1, 'C': 2.03, 'D': 0.6}
delay_cmd = {'A': 'AD', 'B': 'BD', 'C': 'CD', 'D': 'DD'}

def apply_delays(overrides={}):
    for ch in 'ABCD':
        val = overrides.get(ch, origins[ch])
        send_command(f"{delay_cmd[ch]} {val:.3f}n")

def sweep_channel(ch, sweep_ns=3, duration=5, steps=100):
    print(f"⏱️  Animating delay on channel {ch}...")
    d_step = sweep_ns / steps
    sleep_step = duration / (2 * steps)

    for i in range(steps + 1):
        apply_delays({ch: origins[ch] + i * d_step})
        time.sleep(sleep_step)
    for i in range(steps + 1):
        apply_delays({ch: origins[ch] + (sweep_ns - i * d_step)})
        time.sleep(sleep_step)
    print(f"✅ Delay animation done for {ch}\n")

def init_delay_system():
    send_command("TRIGGER POS")
    send_command("DW 2u")
    for cmd in ['ASET', 'BSET', 'CSET', 'DSET']:
        send_command(cmd)
    apply_delays()
    time.sleep(1)

# --- Main Combined Animation ---
def main():
    if not ser.isOpen():
        print("❌ Serial port not open.")
        return

    print("🎬 Starting combined attenuation + delay animation...\n")

    # 1. Attenuation animation
    animate_attenuation()

    # 2. Time delay animation
    init_delay_system()
    for ch in ['C', 'D', 'B']:
        sweep_channel(ch)
        time.sleep(0.5)

    print("🎉 All animations complete.")

if __name__ == "__main__":
    main()

