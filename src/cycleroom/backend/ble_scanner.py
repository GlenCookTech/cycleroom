
import asyncio
import logging
from bleak import BleakScanner
import httpx
import os

# FastAPI Endpoint to Send Parsed Data
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi-app:8000/api/bikes")

# Logger Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Target Device Prefix
TARGET_PREFIX = os.getenv("TARGET_PREFIX", "M3")

# BLE Scanning Function
async def scan_keiser_bikes(scan_duration=10):
    found_bikes = {}

    def detection_callback(device, advertisement_data):
        if device.name and device.name.startswith(TARGET_PREFIX):
            try:
                manufacturer_data = advertisement_data.manufacturer_data.get(0x0645)
                if manufacturer_data:
                    parsed_data = {"device_name": device.name, "device_address": device.address}
                    found_bikes[device.address] = parsed_data
                    logger.info(f"✅ Found Keiser Bike {device.name} ({device.address}) → {parsed_data}")
            except KeyError as e:
                logger.warning(f"⚠️ Error parsing BLE data from {device.name}: {e}")

    scanner = BleakScanner(detection_callback)
    logger.info("🔍 Starting BLE scan...")
    await scanner.start()
    await asyncio.sleep(scan_duration)
    await scanner.stop()
    logger.info(f"🔍 Scan complete. Found {len(found_bikes)} bikes.")

    await send_data_to_fastapi(found_bikes)

# Send Parsed Data to FastAPI Backend
async def send_data_to_fastapi(data):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(FASTAPI_URL, json=data)
            if response.status_code == 200:
                logger.info("✅ Successfully sent BLE data to FastAPI.")
            else:
                logger.error(f"❌ Failed to send BLE data. Status Code: {response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"❌ Error sending data to FastAPI: {e}")

# Main BLE Scanner Loop
async def main():
    while True:
        await scan_keiser_bikes()
        await asyncio.sleep(5)  # Scan every 5 seconds

if __name__ == "__main__":
    asyncio.run(main())
