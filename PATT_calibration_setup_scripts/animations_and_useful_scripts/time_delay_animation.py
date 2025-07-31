import serial
import time
import numpy as np

# Setup serial connection
ser = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=38400,
    timeout=1,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

# Close then reopen to reset
ser.close()
ser.open()

def send_command(cmd, loud=False):
    ser.write(str.encode(cmd + '\n'))
    line = ser.readline().decode().strip()
    if loud:
        print(f"> {cmd} => {line}")
    return line

# Channel label to T660 command prefix
channel_cmd = {'A': 'AD', 'B': 'BD', 'C': 'CD', 'D': 'DD'}

# Origin delays in nanoseconds
origins = {'A': 0.0, 'B': 0.1, 'C': 2.03, 'D': 0.6}  # in ns

# Progressive sweep config
sweep_ns = 2
duration = 0.5  # seconds
steps = 100
delay_step = sweep_ns / steps
sleep_per_step = duration / (2 * steps)  # up and down

def apply_delays(overrides={}):
    for ch in 'ABCD':
        val = overrides.get(ch, origins[ch])
        send_command(f"{channel_cmd[ch]} {val:.3f}n")

def sweep_channel(ch):
    print(f"\n🌀 Animating delay on channel {ch}...")

    # Step 1: sweep forward (origin → +3 ns)
    for i in range(steps + 1):
        delta = i * delay_step
        apply_delays({ch: origins[ch] + delta})
        time.sleep(sleep_per_step)

    # Step 2: sweep back
    for i in range(steps + 1):
        delta = sweep_ns - i * delay_step
        apply_delays({ch: origins[ch] + delta})
        time.sleep(sleep_per_step)

    print(f"✅ Done animating {ch}")

def main():
    if not ser.isOpen():
        print("❌ Serial port not open.")
        return

    print("🎬 Starting time delay animation...")
    send_command("TRIGGER POS")
    send_command("DW 2u")  # pulse width (optional)

    # Ensure all outputs are enabled
    for cmd in ['ASET', 'BSET', 'CSET', 'DSET']:
        send_command(cmd)

    # Set to initial delays
    apply_delays()
    time.sleep(1)

    # Animate channels C, D, B in order
    for ch in ['C', 'D', 'B']:
        sweep_channel(ch)
        time.sleep(0.5)

    print("🎉 Animation complete.")

if __name__ == "__main__":
    main()

