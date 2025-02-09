import asyncio
import os
import json
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, HTTPException
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

# ✅ Import BLE Scanner & Fake Data Generator
from fake_data import generate_realistic_data
from ble_listener import scan_keiser_bikes

# ✅ Load environment variables
load_dotenv()

# ✅ InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://127.0.0.1:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "your_token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "your_org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "your_bucket")

# ✅ Initialize InfluxDB Client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

# ✅ Initialize FastAPI
app = FastAPI()

# ✅ WebSocket for Real-time Updates
connected_clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

# ✅ API Route to Send Fake Data
@app.get("/send_fake_data")
def send_fake_data():
    data = generate_realistic_data()
    create_session(data)
    print(f"📡 Sent realistic fake data: {data}")
    return {"message": "Realistic fake data sent", "data": data}

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
            .field("calories", data["calories"])
            .time(timestamp)
        )

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
                create_session(data)
        else:
            print("⚠️ No bikes found. Sending fake data instead...")
            send_fake_data()

        await asyncio.sleep(5)  # Scan every 5 seconds



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
