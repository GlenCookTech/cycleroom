import json
import requests
import time
import multiprocessing
from collections import defaultdict
from keiser_m3_ble_parser import KeiserM3BLEBroadcast # ✅ Import the parser function


# Load JSON data from file
json_file = "filtered_output.json"
output_file = "parsed_output.json"

with open(json_file, "r") as file:
    data = json.load(file)

# Extract Bluetooth data
bluetooth_records = [entry for entry in data if entry["sensor"] == "Bluetooth"]

server_url = "http://127.0.0.1:8000/sessions"

# ✅ Process records and extract `duration_minutes` & `duration_seconds`
device_records = defaultdict(list)

for record in bluetooth_records:
    manufacturer_data_hex = record.get("manufacturerData", "").strip()

    if not manufacturer_data_hex:
        print(f"⚠️ Skipping record - No manufacturer data")
        continue

    if not all(c in "0123456789abcdefABCDEF" for c in manufacturer_data_hex):
        print(f"❌ Skipping record - Invalid manufacturer data format: {manufacturer_data_hex}")
        continue

    try:
        # Convert hex string to bytes
        manufacturer_data = {0x0645: bytes.fromhex(manufacturer_data_hex)}

        # Parse the manufacturer data
        parsed_data = KeiserM3BLEBroadcast(manufacturer_data)

        if parsed_data and "duration_minutes" in parsed_data and "duration_seconds" in parsed_data and "Equipment_ID" in parsed_data:
            parsed_data["total_duration"] = (parsed_data["duration_minutes"] * 60) + parsed_data["duration_seconds"]

            # ✅ Use `equipment_id` instead of `id`
            equipment_id = str(parsed_data["Equipment_ID"])  # Convert to string for JSON compatibility
            parsed_data["equipment_id"] = equipment_id  # Ensure field name consistency

            device_records[equipment_id].append(parsed_data)  # Group by Equipment ID

        else:
            print(f"⚠️ Skipping record - Missing required fields: {parsed_data}")

    except ValueError as e:
        print(f"🔥 BLE Parsing Error - Data: {manufacturer_data_hex}")
        print(f"   Exception: {e}")

# ✅ Write parsed data to file
with open(output_file, "w") as out_file:
    json.dump(device_records, out_file, indent=4)

print(f"💾 Parsed data saved to {output_file}")

# ✅ Check if device records exist before proceeding
if not device_records:
    print("❌ ERROR: No valid records found for posting! Exiting...")
    exit(1)

# ✅ Function to handle sending data for a single Equipment ID
def process_equipment(equipment_id, records):
    script_start_time = time.time()
    records.sort(key=lambda x: x["total_duration"])  # Sort by event time

    print(f"🚴 Starting process for Equipment {equipment_id} with {len(records)} records...")

    for parsed_data in records:
        total_duration = parsed_data["total_duration"]

        # ✅ Calculate absolute target time based on script start
        target_time = script_start_time + total_duration
        current_time = time.time()
        delay = target_time - current_time

        if delay > 0:
            print(f"⏳ Waiting {delay:.2f} sec before sending data for Equipment {equipment_id}...")
            time.sleep(delay)  # ✅ Ensure correct pacing

        # ✅ Log the request payload before sending
        print(f"📤 Sending data for Equipment {equipment_id}: {json.dumps(parsed_data, indent=2)}")

        response = requests.post(server_url, json=parsed_data)

        if response.status_code == 200:
            print(f"✅ Successfully sent data for Equipment {equipment_id} at {total_duration} seconds")
        else:
            print(f"❌ Failed to send data for Equipment {equipment_id}: {response.text}")
            print(f"❌ Payload Sent: {json.dumps(parsed_data, indent=2)}")  # ✅ Print exactly what was sent

# ✅ Spawn a separate process for each Equipment ID
processes = []
for equipment_id, records in device_records.items():
    p = multiprocessing.Process(target=process_equipment, args=(equipment_id, records))
    p.start()
    processes.append(p)

# ✅ Wait for all processes to complete
for p in processes:
    p.join()

print("✅ All equipment data has been processed.")
