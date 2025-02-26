import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import uvicorn
import psycopg2
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from influxdb_client import InfluxDBClient, Point, WritePrecision
from bleak import BleakScanner

from keiser_m3_ble_parser import KeiserM3BLEBroadcast  # Ensure correct import path

# ✅ Load environment variables
TIMESCALE_HOST = os.getenv("TIMESCALE_HOST", "timescaledb")
TIMESCALE_DB = os.getenv("TIMESCALE_DB", "cycleroom")
TIMESCALE_USER = os.getenv("TIMESCALE_USER", "postgres")
TIMESCALE_PASSWORD = os.getenv("TIMESCALE_PASSWORD", "GlenCookTech78")
TIMESCALE_PORT = os.getenv("TIMESCALE_PORT", "5432")

# ✅ InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "your-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "your-org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "your-bucket")

# ✅ Grafana API Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000/api/annotations")
GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY", "your-api-key")

# ✅ WebSocket connections storage
active_connections = {}

# ✅ Database Connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=TIMESCALE_HOST,
            database=TIMESCALE_DB,
            user=TIMESCALE_USER,
            password=TIMESCALE_PASSWORD,
            port=TIMESCALE_PORT
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        logging.error(f"❌ Database connection error: {e}")
        return None

# ✅ Broadcast updates to WebSocket clients
async def broadcast_ws(data):
    equipment_id = str(data["equipment_id"])
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

# ✅ Store Parsed Data in TimescaleDB & InfluxDB
async def store_bike_data(data):
    """Stores bike data in TimescaleDB & InfluxDB."""
    try:
        timestamp = data.get("timestamp", datetime.utcnow().replace(tzinfo=timezone.utc).isoformat())
        equipment_id = str(data.get("equipment_id", "unknown"))
        power = int(data.get("power", 0))
        cadence = float(data.get("cadence", 0))
        heart_rate = int(data.get("heart_rate", 0))
        gear = int(data.get("gear", 0))
        caloric_burn = int(data.get("caloric_burn", 0))
        duration = int(data.get("duration", 0))
        distance = float(data.get("trip_distance", 0))

        logging.info(f"📝 Storing Data: {json.dumps(data, indent=2)}")

        # ✅ Insert into TimescaleDB
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO keiser_m3 (time, equipment_id, power, cadence, heart_rate, gear, caloric_burn, duration, distance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                cursor.execute(query, (timestamp, equipment_id, power, cadence, heart_rate, gear, caloric_burn, duration, distance))

        # ✅ Insert into InfluxDB
        with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
            write_api = client.write_api()
            point = Point("keiser_m3") \
                .tag("equipment_id", equipment_id) \
                .field("power", power) \
                .field("cadence", cadence) \
                .field("heart_rate", heart_rate) \
                .field("gear", gear) \
                .field("caloric_burn", caloric_burn) \
                .field("duration", duration) \
                .field("distance", distance) \
                .time(timestamp, WritePrecision.NS)
            write_api.write(bucket=INFLUXDB_BUCKET, record=point)

    except Exception as e:
        logging.error(f"🔥 Error Writing to Databases: {e}")

# ✅ FastAPI Setup
app = FastAPI()

# ✅ Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ WebSocket Endpoint
@app.websocket("/ws/{equipment_id}")
async def websocket_endpoint(websocket: WebSocket, equipment_id: str):
    await websocket.accept()
    active_connections.setdload_dotenv(dotenv_path="config/.env")
equipment_id].remove(websocket)
        if not active_connections[equipment_id]:
            del active_connections[equipment_id]

# ✅ API Endpoints
@app.post("/sessions")
async def create_session(data: dict):
    """Receives session data and stores it."""
    if not data:
        raise HTTPException(status_code=400, detail="No data received")
    asyncio.create_task(store_bike_data(data))
    return {"message": "Session saved successfully", "data": data}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ✅ Start the BLE Scanner on App Startup
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

# ✅ Run Server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
