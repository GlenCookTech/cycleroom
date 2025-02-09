import asyncio
import json
from datetime import datetime, timezone
from bleak import BleakScanner

# ✅ BLE Listener Settings
TARGET_PREFIX = "M3"  # Matches Keiser M3 bikes

# ✅ Parse BLE Manufacturer Data
def parse_ble_data(manufacturer_data):
    """Parses Keiser M3 BLE advertisement data using the provided byte structure."""
    try:
        # ✅ Extract raw hex data
        raw_hex = manufacturer_data.get(0x0645, b"").hex()

        if not raw_hex:
            print(f"⚠️ Skipping BLE Parsing - Manufacturer data is empty or missing: {manufacturer_data}")
            return None  # No valid data
        
        print(f"🔍 Parsing BLE Data: {raw_hex}")  # Debugging log

        # Ensure data has the required length (19 bytes expected)
        if len(raw_hex) < 19 * 2:  # Each byte is represented by 2 hex characters
            print(f"⚠️ Skipping Parsing - Incomplete Data: {raw_hex} (length: {len(raw_hex)})")
            return None

        # 🔍 Extract fields based on table structure
        parsed_data = {
            "Company_ID": raw_hex[0:4],  # Byte 0, 1 (Company ID)
            "Version_Major": int(raw_hex[4:6], 16),  # Byte 2
            "Version_Minor": int(raw_hex[6:8], 16),  # Byte 3
            "Data_Type": int(raw_hex[8:10], 16),  # Byte 4
            "Equipment_ID": int(raw_hex[10:12], 16),  # Byte 5
            "Cadence": int(raw_hex[12:16], 16),  # Byte 6, 7
            "Heart_Rate": int(raw_hex[16:20], 16),  # Byte 8, 9
            "Power": int(raw_hex[20:24], 16),  # Byte 10, 11
            "Caloric_Burn": int(raw_hex[24:28], 16),  # Byte 12, 13
            "Duration_Minutes": int(raw_hex[28:30], 16),  # Byte 14
            "Duration_Seconds": int(raw_hex[30:32], 16),  # Byte 15
            "Distance": float(int(raw_hex[32:36], 16) / 100.0),  # Byte 16, 17 (convert to float)
            "Gear": int(raw_hex[36:38], 16),  # Byte 18
        }

        return {
            "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            "power": parsed_data["Power"],
            "cadence": parsed_data["Cadence"],
            "heart_rate": parsed_data["Heart_Rate"],
            "gear": parsed_data["Gear"],
            "caloric_burn": parsed_data["Caloric_Burn"],
            "duration_minutes": parsed_data["Duration_Minutes"],
            "duration_seconds": parsed_data["Duration_Seconds"],
            "distance": parsed_data["Distance"]
        }

    except Exception as e:
        print(f"🔥 BLE Parsing Error: {e} - Raw Data: {manufacturer_data}")
        return None
    
# ✅ BLE Detection Callback
async def scan_keiser_bikes():
    found_bikes = {}

    def detection_callback(device, advertisement_data):
        if device.name and device.name.startswith(TARGET_PREFIX):
            parsed_data = parse_ble_data(advertisement_data.manufacturer_data)
            if parsed_data:
                found_bikes[device.address] = parsed_data

    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(5)  # Scan for 5 seconds
    await scanner.stop()

    return found_bikes
