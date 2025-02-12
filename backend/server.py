import os
import json
import asyncio
import uvicorn
import psycopg2
from influxdb_client import InfluxDBClient, Point, WritePrecision
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from bleak import BleakScanner
from keiser_m3_ble_parser import KeiserM3BLEBroadcast  # ✅ Improved BLE Parser

# ✅ Load environment variables
load_dotenv()
TIMESCALE_HOST = os.getenv("TIMESCALE_HOST", "localhost")
TIMESCALE_DB = os.getenv("TIMESCALE_DB", "cycleroom")
TIMESCALE_USER = os.getenv("TIMESCALE_USER", "postgres")
TIMESCALE_PASSWORD = os.getenv("TIMESCALE_PASSWORD", "password")
TIMESCALE_PORT = os.getenv("TIMESCALE_PORT", "5432")

# ✅ InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "your-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "your-org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "your-bucket")

# ✅ WebSocket connections storage
active_connections = {}

# ✅ Connect to TimescaleDB
def get_db_connection():
    conn = psycopg2.connect(
        host=TIMESCALE_HOST,
        database=TIMESCALE_DB,
        user=TIMESCALE_USER,
        password=TIMESCALE_PASSWORD,
        port=TIMESCALE_PORT
    )
    conn.autocommit = True  # Force commit to database
    return conn

# ✅ Initialize FastAPI
app = FastAPI()

# ✅ Configure CORS to allow WebSocket connections from Grafana
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ WebSocket Endpoint for Real-Time Streaming per Equipment
@app.websocket("/ws/{equipment_id}")
async def websocket_endpoint(websocket: WebSocket, equipment_id: str):
    await websocket.accept()
    if equipment_id not in active_connections:
        active_connections[equipment_id] = set()
    active_connections[equipment_id].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if equipment_id in active_connections and websocket in active_connections[equipment_id]:
            active_connections[equipment_id].remove(websocket)
            if not active_connections[equipment_id]:  # Cleanup empty connection lists
                del active_connections[equipment_id]

# ✅ Broadcast updates to WebSocket clients per Equipment
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

# ✅ BLE Detection & Parsing Loop
async def continuous_ble_scanner():
    """Continuously scans for Keiser M3 bikes and processes BLE data."""
    TARGET_PREFIX = "M3"

    def detection_callback(device, advertisement_data):
        if device.name and device.name.startswith(TARGET_PREFIX):
            try:
                parsed_data = KeiserM3BLEBroadcast(advertisement_data.manufacturer_data[0x0645]).to_dict()

                # ✅ Store Data in TimescaleDB & InfluxDB
                asyncio.create_task(store_bike_data(parsed_data))
            except Exception as e:
                print(f"⚠️ Error parsing BLE data from {device.name}: {e}")

    scanner = BleakScanner(detection_callback)

    while True:
        print("🔍 Scanning for Keiser M3 bikes...")
        await scanner.start()
        await asyncio.sleep(10)  # Scan duration (10 seconds)
        await scanner.stop()
        print("🔍 Scan cycle completed. Restarting...")

# ✅ Store Parsed Data in TimescaleDB & InfluxDB
async def store_bike_data(data):
    try:
        timestamp = datetime.utcnow().replace(tzinfo=timezone.utc)

        # ✅ Extract Data Fields
        equipment_id = str(data["equipment_id"])
        power = int(data["power"])
        cadence = float(data["cadence"]) / 10.0  # Convert 0.1 RPM to RPM
        heart_rate = int(data["heart_rate"])
        gear = int(data["gear"])
        caloric_burn = int(data["caloric_burn"])
        duration = int(data.get("duration", 0))
        distance = float(data["trip_distance"])  # Ensure proper distance handling

        # ✅ Insert into TimescaleDB
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO keiser_m3 (time, equipment_id, power, cadence, heart_rate, gear, caloric_burn, duration, distance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                values = (timestamp, equipment_id, power, cadence, heart_rate, gear, caloric_burn, duration, distance)
                cursor.execute(query, values)

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

        print(f"✅ Stored bike data: {data}")
        await broadcast_ws(data)

    except Exception as e:
        print(f"🔥 Error Writing to Databases: {e}")

# ✅ Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ✅ Start FastAPI Server & Background Scanner
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(continuous_ble_scanner())  # ✅ Run BLE scanner in the background
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
