import json
import requests
import time
from cycleroom.backend.keiser_m3_ble_parser import KeiserM3BLEBroadcast  # ✅ Import the new parser

# Load JSON data from file
json_file = "filtered_output.json"

with open(json_file, "r") as file:
    data = json.load(file)

# Extract Bluetooth data
#bluetooth_records = [entry for entry in data if entry["sensor"] == "Bluetooth"]
bluetooth_records = [entry for entry in data]  # ✅ Use lowercase for comparison

# Sort records by time (to ensure correct scheduling)
bluetooth_records.sort(key=lambda x: float(x["seconds_elapsed"]))

server_url = "http://127.0.0.1:8000/sessions"

# Get start time to sync delays
start_time = time.time()

# Process records one by one
for index, record in enumerate(bluetooth_records):
    manufacturer_data_hex = record.get("manufacturerData", "").strip()
    bluetooth_mac = record.get("id", "UNKNOWN_DEVICE")  # ✅ Keep original MAC address for reference

    # ✅ Skip if `manufacturerData` is missing or empty
    if not manufacturer_data_hex:
        print(f"⚠️ Skipping device {bluetooth_mac} - No manufacturer data")
        continue

    # ✅ Skip invalid hex format
    if not all(c in "0123456789abcdefABCDEF" for c in manufacturer_data_hex):
        print(f"❌ Skipping device {bluetooth_mac} - Invalid manufacturer data format: {manufacturer_data_hex}")
        continue

    try:
        # Convert hex string to bytes
        manufacturer_data_bytes = bytes.fromhex(manufacturer_data_hex)

        # ✅ Parse the manufacturer data
        parsed_data = KeiserM3BLEBroadcast(manufacturer_data_bytes).to_dict()

        if parsed_data:
            # ✅ Extract the correct `equipment_id` from parsed data
            equipment_id = str(parsed_data.get("ordinal_id", bluetooth_mac))  # Use `ordinal_id` if available, else MAC
            parsed_data["equipment_id"] = equipment_id  # ✅ Use extracted Equipment ID
            parsed_data["bluetooth_mac"] = bluetooth_mac  # ✅ Keep original MAC for reference

            # ✅ Calculate Delay Based on `seconds_elapsed`
            elapsed_time = float(record["seconds_elapsed"])
            current_time = time.time()
            delay = max(0, start_time + elapsed_time - current_time)

            print(f"⏳ Waiting {delay:.2f} sec before sending data for Equipment {equipment_id}...")
            time.sleep(delay)  # Wait to match `seconds_elapsed`

            # ✅ Send parsed data to the server
            response = requests.post(server_url, json=parsed_data)

            if response.status_code == 200:
                print(f"✅ Successfully sent data for Equipment {equipment_id}")
            else:
                print(f"❌ Failed to send data for {equipment_id}: {response.text}")

    except Exception as e:
        print(f"🔥 BLE Parsing Error for device {bluetooth_mac} - Data: {manufacturer_data_hex}")
        print(f"   Exception: {e}")
