import asyncio
from bleak import BleakScanner
from keiser_m3_ble_parser import KeiserM3BLEBroadcast  # ✅ Import the improved parser

# ✅ BLE Listener Settings
TARGET_PREFIX = "M3"

async def scan_keiser_bikes(scan_duration=10):
    """Scan for Keiser M3 bikes and parse BLE advertisement data."""
    found_bikes = {}

    def detection_callback(device, advertisement_data):
        if device.name and device.name.startswith(TARGET_PREFIX):
            try:
                parsed_data = KeiserM3BLEBroadcast(advertisement_data.manufacturer_data[0x0645]).to_dict()
                if parsed_data:
                    found_bikes[device.address] = parsed_data
                    print(f"✅ Found Keiser Bike {device.name} ({device.address}) → {parsed_data}")
            except Exception as e:
                print(f"⚠️ Error parsing BLE data from {device.name}: {e}")

    scanner = BleakScanner(detection_callback)
    
    print("🔍 Starting BLE scan...")
    await scanner.start()
    await asyncio.sleep(scan_duration)  # ✅ Scan for 10 seconds instead of 5
    await scanner.stop()
    print(f"🔍 Scan complete. Found {len(found_bikes)} bikes.")

    if not found_bikes:
        print("⚠️ No Keiser bikes found. Ensure they are powered on and broadcasting.")

    return found_bikes

# ✅ Example usage (run only in an async environment)
if __name__ == "__main__":
    asyncio.run(scan_keiser_bikes())
