# Re-import necessary modules after kernel reset
import json
import matplotlib.pyplot as plt

# Re-define file path
file_path = "deep_impulse_responses.json"

# Attempt to read it as JSON even though it has a .png extension (user context suggests it's a dictionary)
try:
    with open(file_path, "r") as f:
        data = json.load(f)

    # Extract relevant fields
    time = data.get('time', [])
    ch2_2x_amp = data.get('ch2_2x_amp', [])

    # Plot and save
    plt.figure(figsize=(10, 4))
    plt.plot(time, ch2_2x_amp, linewidth=1.5)
    plt.title("Channel 2 Amplitude vs Time")
    plt.xlabel("Time (ns)")
    plt.ylabel("Amplitude (a.u.)")
    plt.grid(True)
    plt.tight_layout()

    output_path = "ch2_plot.png"
    plt.savefig(output_path)

    output_path

except Exception as e:
    str(e)

