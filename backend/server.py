import os
import json
import redis
import asyncio
import uvicorn
from fake_data import generate_realistic_data
from ble_listener import scan_keiser_bikes
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone

# Load environment variables
load_dotenv()
INFLUX_HOST = os.getenv("INFLUX_HOST")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

if not INFLUX_HOST or not INFLUX_TOKEN or not INFLUX_ORG:
    raise ValueError("🚨 InfluxDB environment variables are missing! Check .env file.")

# Initialize FastAPI
app = FastAPI()

# Configure CORS to allow WebSocket connections from Grafana
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize InfluxDB
client = InfluxDBClient(url=INFLUX_HOST, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

# WebSocket connections storage
active_connections = {}

# ✅ Store session data in InfluxDB
@app.post("/sessions")
async def create_session(data: dict):
    required_keys = ["equipment_id", "timestamp", "power", "gear", "distance", "cadence", "heart_rate", "caloric_burn", "duration_minutes", "duration_seconds"]
    if not all(key in data for key in required_keys):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        # ✅ Convert timestamp from JSON input
        timestamp = datetime.fromisoformat(data["timestamp"]).replace(tzinfo=timezone.utc)

        # ✅ Create InfluxDB data point
        point = (
            Point("keiser_m3")
            .tag("equipment_id", str(data["equipment_id"]))  # Ensure it's a string for InfluxDB
            .field("power", int(data["power"]))
            .field("cadence", int(data["cadence"]))
            .field("heart_rate", int(data["heart_rate"]))
            .field("gear", int(data["gear"]))
            .field("caloric_burn", int(data["caloric_burn"]))  # 🔥 Ensure this is an integer
            .field("duration_minutes", int(data["duration_minutes"]))
            .field("duration_seconds", int(data["duration_seconds"]))
            .field("distance", int(data["distance"]))
            .time(datetime.utcnow().replace(tzinfo=timezone.utc)) 
        )

        # ✅ Write to InfluxDB
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

        # ✅ Broadcast new data to WebSocket clients
        await broadcast_ws(data)

    except Exception as e:
        print(f"🔥 Error Writing to InfluxDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Session saved successfully", "data": data}

# ✅ WebSocket Endpoint for Real-Time Streaming per Equipment
@app.websocket("/ws/{equipment_id}")
async def websocket_endpoint(websocket: WebSocket, equipment_id: str):
    await websocket.accept()
    if equipment_id not in active_connections:
        active_connections[equipment_id] = set()
    active_connections[equipment_id].add(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        active_connections[equipment_id].remove(websocket)
        if not active_connections[equipment_id]:
            del active_connections[equipment_id]

# ✅ Broadcast updates to WebSocket clients per Equipment
async def broadcast_ws(data):
    equipment_id = str(data["equipment_id"])  # ✅ Fix mismatch
    message = {
        "power": data["power"],
        "gear": data["gear"],
        "distance": data["distance"],
        "cadence": data["cadence"],
        "heart_rate": data["heart_rate"],
        "caloric_burn": data["caloric_burn"],
        "timestamp": data["timestamp"]
    }
    if equipment_id in active_connections:
        for websocket in active_connections[equipment_id]:
            await websocket.send_json(message)

# ✅ Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ✅ Start FastAPI Server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
