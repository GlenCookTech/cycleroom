import pandas as pd
import json
from datetime import datetime, timedelta

# File Paths
metadata_file = "BluetoothMetadata.csv"
json_file = "2025-02-09_17-11-56.json"
output_file = "filtered_output.json"

# ✅ Load the Bluetooth metadata CSV
metadata_df = pd.read_csv(metadata_file)

# ✅ Extract device IDs where `name` is "M3"
m3_device_ids = set(metadata_df.loc[metadata_df["name"] == "M3", "id"].dropna())

# ✅ Load JSON file
with open(json_file, "r", encoding="utf-8") as file:
    json_data = json.load(file)

# Count before filtering
before_count = len(json_data)

# ✅ Filter JSON records to keep only M3 Bluetooth devices
filtered_json_data = []
valid_times = []
for entry in json_data:
    entry_time_ns = entry.get("time")
    if entry_time_ns:
        try:
            entry_time = datetime.utcfromtimestamp(int(entry_time_ns) / 1e9)  # Convert nanoseconds to seconds
            valid_times.append(entry_time)
            if entry.get("sensor") != "Bluetooth" or entry.get("id") in m3_device_ids:
                filtered_json_data.append(entry)
        except ValueError:
            continue  # Skip entries with invalid time format

# Count after filtering
after_count = len(filtered_json_data)

# Compute time difference if valid times exist
if valid_times:
    first_time = min(valid_times)
    last_time = max(valid_times)
    time_difference = last_time - first_time
    print(f"🕒 First record time: {first_time}")
    print(f"🕒 Last record time: {last_time}")
    print(f"⏳ Time difference: {time_difference}")

# ✅ Save the filtered JSON data
with open(output_file, "w", encoding="utf-8") as file:
    json.dump(filtered_json_data, file, indent=4)

# Display results
print(f"📊 Records before filtering: {before_count}")
print(f"✅ Records after filtering: {after_count}")
print(f"💾 Filtered JSON saved as: {output_file}")
