import os
import json
import redis
import asyncio
import uvicorn
from fake_data import generate_realistic_data
from ble_listener import scan_keiser_bikes

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv(dotenv_path="./backend/.env")

# Debugging: Print InfluxDB Variables
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

if not INFLUXDB_URL or not INFLUXDB_TOKEN or not INFLUXDB_ORG:
    raise ValueError("🚨 InfluxDB environment variables are missing! Check .env file.")

# Initialize FastAPI **(Only one instance!)**
app = FastAPI()

# Initialize Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0)

# Initialize InfluxDB
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# ✅ Fix: `/sessions` Route (Honor Original Timestamp)
@app.post("/sessions")
def create_session(data: dict):
    required_keys = ["device", "timestamp", "power", "cadence", "heart_rate", "gear", "caloric_burn", "duration_minutes", "duration_seconds", "distance"]
    if not all(key in data for key in required_keys):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        # ✅ Convert original timestamp from JSON input
        timestamp = datetime.fromisoformat(data["timestamp"]).replace(tzinfo=timezone.utc)

        # ✅ Create InfluxDB data point (Correct chaining)
        point = (
            Point("keiser_m3")
            .tag("device", data["device"])
            .field("power", int(data["power"]))
            .field("cadence", int(data["cadence"]))
            .field("heart_rate", int(data["heart_rate"]))
            .field("gear", int(data["gear"]))
            .field("caloric_burn", int(data["caloric_burn"]))  # 🔥 Ensure this is an integer
            .field("duration_minutes", int(data["duration_minutes"]))
            .field("duration_seconds", int(data["duration_seconds"]))
            .field("distance", float(data["distance"]))
            .time(timestamp)
        )


        # ✅ Write to InfluxDB
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

    except Exception as e:
        print(f"🔥 Error Writing to InfluxDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Session saved successfully", "data": data}

# ✅ Function to Scan BLE & Send Data
async def scan_and_store_data():
    while True:
        print("🔍 Scanning for Keiser M3 Bikes...")
        bikes = await scan_keiser_bikes()

        if bikes:
            print(f"✅ Found {len(bikes)} bike(s)! Storing real data...")
            for device, data in bikes.items():
                data["device"] = device
                await asyncio.to_thread(create_session, data)
        else:
            print("⚠️ No bikes found. Sending fake data instead...")
            generate_realistic_data()

        await asyncio.sleep(5)

# ✅ Health Check
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ✅ Use `lifespan` Correctly (No Duplicate `app`)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚴‍♂️ Starting BLE Scanner & Fake Data Generator...")
    asyncio.create_task(scan_and_store_data())
    yield
    print("🛑 Shutting Down BLE Scanner...")

# ✅ Assign lifespan to existing app instance
app.router.lifespan_context = lifespan

# ✅ Start FastAPI Server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888, reload=True)
