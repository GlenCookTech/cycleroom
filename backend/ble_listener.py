import asyncio
import json
from datetime import datetime, timezone
from bleak import BleakScanner

# ✅ BLE Listener Settings
TARGET_PREFIX = "M3"  # Matches Keiser M3 bikes

# ✅ Parse BLE Manufacturer Data
def parse_ble_data(manufacturer_data):
    """Parses Keiser M3 BLE advertisement data."""
    try:
        raw_hex = manufacturer_data.get(0x0645, b"").hex()
        if not raw_hex:
            return None  # No valid data

        # 🔍 Example Data Format (Hex): 0645ff0cc801000006000000001e000001
        parsed_data = {
            "Power": int(raw_hex[4:8], 16),
            "Cadence": int(raw_hex[8:10], 16),
            "Heart_Rate": int(raw_hex[10:12], 16),
            "Gear": int(raw_hex[12:14], 16),
            "Caloric_Burn": int(raw_hex[14:16], 16),
            "Duration_Minutes": int(raw_hex[16:18], 16),
            "Duration_Seconds": int(raw_hex[18:20], 16),
            "Distance": float(int(raw_hex[20:24], 16) / 100.0)  # Convert to float
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
        print(f"🔥 BLE Parsing Error: {e}")
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
