import json
import os


def summarize_json(data, indent=0):
    spacing = "  " * indent
    if isinstance(data, dict):
        print(f"{spacing}Dictionary with {len(data)} keys:")
        for key in list(data.keys())[:5]:  # Limit preview to first 5 keys
            value = data[key]
            print(f"{spacing}  - Key: '{key}' → Type: {type(value).__name__}")
            if isinstance(value, (dict, list)):
                summarize_json(value, indent + 2)
    elif isinstance(data, list):
        print(f"{spacing}List with {len(data)} items")
        if data:
            print(f"{spacing}  First item preview:")
            summarize_json(data[0], indent + 2)
    else:
        print(f"{spacing}{type(data).__name__}: {str(data)[:60]}{'...' if len(str(data)) > 60 else ''}")


def make_mini_report(json_path):
    if not os.path.exists(json_path):
        print(f"File does not exist: {json_path}")
        return
    
    print(f"\nOpening JSON file at: {json_path}")
    with open(json_path, 'r') as file:
        data = json.load(file)

    print("\n=== MINI REPORT ===")
    summarize_json(data)
    print("\n=== END OF REPORT ===")

# Path to your file
json_file_path = 'deep_impulse_responses.json'

# Run the report
make_mini_report(json_file_path)

