import asyncio
import os
import json
import random
import math
import time
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, HTTPException
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

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

# ✅ Store Connected WebSockets for Live Data
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

# ✅ Simulated Rider State
rider_state = {
    "power": 100,  # Watts
    "cadence": 80,  # RPM
    "heart_rate": 120,  # BPM
    "gear": 10,  # Start in mid-range gear
    "calories": 0.0,
    "session_start": datetime.utcnow(),
}

# ✅ Function to Generate Realistic Fake Data
def generate_realistic_data():
    elapsed_time = (datetime.utcnow() - rider_state["session_start"]).seconds

    # 🚴‍♂️ Simulate Warm-up
    if elapsed_time < 300:
        rider_state["power"] += random.randint(-5, 10)
        rider_state["cadence"] += random.randint(-2, 5)
    # 🚀 Simulate Steady Ride
    elif elapsed_time < 1800:
        rider_state["power"] += random.randint(-10, 10)
        rider_state["cadence"] += random.randint(-3, 3)
    # 🏁 Simulate Cooldown
    else:
        rider_state["power"] -= random.randint(5, 15)
        rider_state["cadence"] -= random.randint(3, 8)

    # ✅ Boundaries for realistic values
    rider_state["power"] = max(50, min(300, rider_state["power"]))
    rider_state["cadence"] = max(60, min(110, rider_state["cadence"]))

    # ❤️ Simulate Heart Rate
    rider_state["heart_rate"] = min(
        190,
        max(100, rider_state["heart_rate"] + math.ceil(rider_state["power"] / 50) + random.randint(-2, 5))
    )

    # 🔧 Adjust Gear Based on Cadence
    if rider_state["cadence"] > 95:
        rider_state["gear"] = min(24, rider_state["gear"] + 1)
    elif rider_state["cadence"] < 75:
        rider_state["gear"] = max(1, rider_state["gear"] - 1)

    # 🔥 Calories Calculation
    rider_state["calories"] += round((rider_state["power"] * 0.00024), 2)

    return {
        "device": "F5:FC:73:B9:9E:CA",
        "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        "power": rider_state["power"],
        "cadence": rider_state["cadence"],
        "heart_rate": rider_state["heart_rate"],
        "gear": rider_state["gear"],
        "calories": round(rider_state["calories"], 2),
    }

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
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO 8601 format.")

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

    return {"message": "Session saved successfully", "data": data}

# ✅ Query Data from InfluxDB
@app.get("/sessions")
def get_all_sessions():
    query = f'''
        from(bucket: "{INFLDB_BUCKET}")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "keiser_m3")
    '''
    tables = query_api.query(query, org=INFLUXDB_ORG)

    sessions = []
    for table in tables:
        for record in table.records:
            sessions.append({
                "time": record.get_time(),
                "device": record["device"],
                "power": record.get_value(),
                "cadence": record.get_value(),
                "heart_rate": record.get_value(),
                "gear": record.get_value(),
                "calories": record.get_value()
            })

    return sessions

# ✅ Asynchronous Function to Simulate Ride Data
async def simulate_ride():
    while True:
        send_fake_data()
        await asyncio.sleep(5)  # ✅ Send data every 5 seconds

# ✅ Register Startup Event for Background Task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulate_ride())  # ✅ Now correctly runs inside the event loop

# ✅ Start FastAPI Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
