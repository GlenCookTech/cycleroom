import pandas as pd
import json

# File Paths (Update these if needed)
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

# ✅ Filter JSON records to keep only M3 Bluetooth devices
filtered_json_data = [
    entry for entry in json_data if entry.get("sensor") != "Bluetooth" or entry.get("id") in m3_device_ids
]

# ✅ Save the filtered JSON data
with open(output_file, "w", encoding="utf-8") as file:
    json.dump(filtered_json_data, file, indent=4)

print(f"✅ Filtered JSON saved as {output_file}")
