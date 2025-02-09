import os
import json
import redis
import asyncio
import uvicorn
# ✅ Import BLE Scanner & Fake Data Generator
from fake_data import generate_realistic_data
from ble_listener import scan_keiser_bikes

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone  # Ensure this is included
from contextlib import asynccontextmanager  # Add this line

# Load .env file
load_dotenv(dotenv_path="./backend/.env")

# Environment Variables
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

# Initialize FastAPI
app = FastAPI()

# Initialize Redis for caching
redis_client = redis.Redis(host="localhost", port=6379, db=0)

# InfluxDB Client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)  # Add this line
query_api = client.query_api()
# ✅ Store Data in InfluxDB
@app.post("/sessions")
def create_session(data: dict):
    required_keys = ["device", "timestamp", "power", "cadence", "heart_rate", "gear", "calories"]
    if not all(key in data for key in required_keys):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")).astimezone(timezone.utc)

        point = (
            Point("keiser_m3")
            .tag("device", data["device"])
            .field("power", data["power"])
            .field("cadence", data["cadence"])
            .field("heart_rate", data["heart_rate"])
            .field("gear", data["gear"])
            .field("caloric_burn", data["caloric_burn"])
            .field("duration_minutes"), data["duration_minutes"]
            .field("duration_seconds"), data["durations_seconds"]
            .field("distance"), data["distance"]
            .time(timestamp)
        )

        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

    except Exception as e:
        print(f"🔥 Error Writing to InfluxDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Session saved successfully", "data": data}


# ✅ Function to Scan BLE & Send Data

# Update the create_session call in the async function
async def scan_and_store_data():
    while True:
        print("🔍 Scanning for Keiser M3 Bikes...")
        bikes = await scan_keiser_bikes()

        if bikes:
            print(f"✅ Found {len(bikes)} bike(s)! Storing real data...")
            for device, data in bikes.items():
                data["device"] = device
                await asyncio.to_thread(create_session, data)  # Use asyncio.to_thread
        else:
            print("⚠️ No bikes found. Sending fake data instead...")
            generate_realistic_data()

        await asyncio.sleep(5)  # Scan every 5 seconds
### ✅ **API Endpoint with Caching**
@app.get("/gear")
async def get_gear_data():
    """Get gear data from InfluxDB with caching"""
    cache_key = "gear_data"
    
    # Check Redis cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

### ✅ **Health Check for Load Balancers**
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}


# ✅ Use `lifespan` Instead of `@app.on_event("startup")`
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚴‍♂️ Starting BLE Scanner & Fake Data Generator...")
    asyncio.create_task(scan_and_store_data())  # ✅ Runs BLE scan & fallback fake data
    yield
    print("🛑 Shutting Down BLE Scanner...")

# ✅ Initialize FastAPI with `lifespan`
app = FastAPI(lifespan=lifespan)


# ✅ Start FastAPI Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
