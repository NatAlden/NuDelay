import json

json_path = '/mnt/labdata/chicago-rnog-system-response-2024/sys_response_radiant_v3/ch3_response_deep_atten62.json'

with open(json_path) as f:
    data = json.load(f)

print("Keys in first item:")
for key in data[0].keys():
    print("-", key)


example = data[0]

if 'radiant_waveforms' in example:
    print("Radiant response preview:", example['radiant_waveforms'][:10])

if 'station' in example:
    print("Stations:", example['station'])


