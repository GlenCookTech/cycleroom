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
        power = int(raw_hex[4:8], 16)  # Convert from Hex to Int
        cadence = int(raw_hex[8:10], 16)
        heart_rate = int(raw_hex[10:12], 16)
        gear = int(raw_hex[12:14], 16)

        return {
            "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            "power": power,
            "cadence": cadence,
            "heart_rate": heart_rate,
            "gear": gear,
            "calories": round((power * 0.00024), 2),  # Calories estimation
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
