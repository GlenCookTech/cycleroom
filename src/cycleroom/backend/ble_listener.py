import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from bleak import BleakScanner
from cycleroom.backend.keiser_m3_ble_parser import KeiserM3BLEBroadcast

TARGET_PREFIX = "M3"

async def scan_keiser_bikes(scan_duration=10):
    # (Same scanning code as before)
    found_bikes = {}
    def detection_callback(device, advertisement_data):
        if device.name and device.name.startswith(TARGET_PREFIX):
            try:
                parsed_data = KeiserM3BLEBroadcast(advertisement_data.manufacturer_data[0x0645]).to_dict()
                if parsed_data:
                    found_bikes[device.address] = parsed_data
                    logger.info(f"✅ Found Keiser Bike {device.name} ({device.address}) → {parsed_data}")
            except KeyError as e:
                logger.info(f"⚠️ Error parsing BLE data from {device.name}: {e}")
    scanner = BleakScanner(detection_callback)
    logger.info("🔍 Starting BLE scan...")
    await scanner.start()
    await asyncio.sleep(scan_duration)
    await scanner.stop()
    logger.info(f"🔍 Scan complete. Found {len(found_bikes)} bikes.")
    return found_bikes

# Define a continuous scanner that repeatedly scans
async def continuous_ble_scanner():
    while True:
        await scan_keiser_bikes()
        await asyncio.sleep(5)  # wait 5 seconds before next scan

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 Starting FastAPI application")
    scanner_task = asyncio.create_task(continuous_ble_scanner())
    yield
    scanner_task.cancel()
    try:
        await scanner_task
    except asyncio.CancelledError:
        logging.info("🚦 BLE scanner task cancelled cleanly.")

app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ble_listener:app", host="127.0.0.1", port=8002, reload=True)
