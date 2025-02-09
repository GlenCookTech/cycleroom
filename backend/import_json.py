import json
import requests
import time
from ble_listener import parse_ble_data

# Load JSON data from file
json_file = "filtered_output.json"

with open(json_file, "r") as file:
    data = json.load(file)

# Extract Bluetooth data
bluetooth_records = [entry for entry in data if entry["sensor"] == "Bluetooth"]

# Sort records by time (to ensure correct scheduling)
bluetooth_records.sort(key=lambda x: float(x["seconds_elapsed"]))

server_url = "http://127.0.0.1:8888/sessions"

# Get start time to sync delays
start_time = time.time()

# Process records one by one
for index, record in enumerate(bluetooth_records):
    manufacturer_data_hex = record.get("manufacturerData", "").strip()
    device_id = record.get("id", "UNKNOWN_DEVICE")

    # ✅ Log & Skip if `manufacturerData` is missing or empty
    if not manufacturer_data_hex:
        print(f"⚠️ Skipping device {device_id} - No manufacturer data")
        continue

    # ✅ Log & Skip invalid hex format
    if not all(c in "0123456789abcdefABCDEF" for c in manufacturer_data_hex):
        print(f"❌ Skipping device {device_id} - Invalid manufacturer data format: {manufacturer_data_hex}")
        continue

    try:
        # Convert hex string to bytes
        manufacturer_data = {0x0645: bytes.fromhex(manufacturer_data_hex)}

        # Parse the manufacturer data
        parsed_data = parse_ble_data(manufacturer_data)

        if parsed_data:
            parsed_data["device"] = device_id  # Add device MAC address

            # **Calculate Delay Based on `seconds_elapsed`**
            elapsed_time = float(record["seconds_elapsed"])
            current_time = time.time()
            delay = max(0, start_time + elapsed_time - current_time)

            print(f"⏳ Waiting {delay:.2f} sec before sending data for {device_id}...")
            time.sleep(delay)  # Wait to match `seconds_elapsed`

            response = requests.post(server_url, json=parsed_data)

            if response.status_code == 200:
                print(f"✅ Successfully sent data for device {device_id}")
            else:
                print(f"❌ Failed to send data for {device_id}: {response.text}")

    except ValueError as e:
        print(f"🔥 BLE Parsing Error for device {device_id} - Data: {manufacturer_data_hex}")
        print(f"   Exception: {e}")
