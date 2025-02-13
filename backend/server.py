import os
import json
import asyncio
import uvicorn
import psycopg2
import logging
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
    """Stores bike data in TimescaleDB & InfluxDB."""
    try:
        timestamp = data.get("timestamp", datetime.utcnow().replace(tzinfo=timezone.utc).isoformat())
        equipment_id = str(data.get("equipment_id", "unknown"))
        power = int(data.get("power", 0))
        cadence = float(data.get("cadence", 0))  # Convert 0.1 RPM to RPM
        heart_rate = int(data.get("heart_rate", 0))
        gear = int(data.get("gear", 0))
        caloric_burn = int(data.get("caloric_burn", 0))
        duration = int(data.get("duration", 0))
        distance = float(data.get("trip_distance", 0))  # ✅ Use `trip_distance` as fallback for `distance`

        # ✅ Log the parsed data for debugging
        logging.info(f"📝 Storing Data: {json.dumps(data, indent=2)}")

        # ✅ Insert into TimescaleDB
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO keiser_m3 (time, equipment_id, power, cadence, heart_rate, gear, caloric_burn, duration, distance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                values = (timestamp, equipment_id, power, cadence, heart_rate, gear, caloric_burn, duration, distance)
                cursor.execute(query, values)
                conn.commit()
                logging.info(f"✅ Data inserted into TimescaleDB for {equipment_id}")

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
            logging.info(f"✅ Data inserted into InfluxDB for {equipment_id}")

    except Exception as e:
        logging.error(f"🔥 Error Writing to Databases: {e}")

app = FastAPI()

@app.post("/sessions")
async def create_session(data: dict):
    """Receives session data and stores it using `store_bike_data()`."""
    logging.info(f"📥 Incoming Session Data: {data}")

    if not data:
        raise HTTPException(status_code=400, detail="No data received")

    try:
        # ✅ Call `store_bike_data` to handle data storage
        asyncio.create_task(store_bike_data(data))  # Run in background

        return {"message": "Session saved successfully", "data": data}

    except Exception as e:
        logging.error(f"🔥 Error storing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

# ✅ Grafana API Configuration
GRAFANA_URL = "http://localhost:3000/api/annotations"
GRAFANA_API_KEY = "your-grafana-api-key"  # 🔹 Replace with your real API key

# ✅ Connect to PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        host=TIMESCALE_HOST,
        database=TIMESCALE_DB,
        user=TIMESCALE_USER,
        password=TIMESCALE_PASSWORD,
        port=TIMESCALE_PORT
    )

# ✅ Create the `bike_selections` Table (If Not Exists)
def create_bike_table():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bike_selections (
                    id SERIAL PRIMARY KEY,
                    user_name TEXT NOT NULL,
                    equipment_id INT NOT NULL,
                    timestamp TIMESTAMPTZ DEFAULT now()
                );
            """)
            conn.commit()

create_bike_table()  # 🔹 Ensure table exists at startup

# ✅ Store Bike Selection
@app.post("/update_grafana")
async def update_grafana(data: dict):
    """Updates PostgreSQL & Grafana with the selected bike info."""
    user_name = data.get("user_name")
    equipment_id = data.get("equipment_id")

    if not user_name or not equipment_id:
        raise HTTPException(status_code=400, detail="Missing user_name or equipment_id")

    try:
        # ✅ Insert into PostgreSQL
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO bike_selections (user_name, equipment_id) VALUES (%s, %s);",
                    (user_name, equipment_id)
                )
                conn.commit()

        logging.info(f"✅ Stored {user_name} on Bike {equipment_id} in PostgreSQL")

        # ✅ Send Update to Grafana
        grafana_data = {
            "text": f"🚴‍♂️ {user_name} is now on Bike {equipment_id}",
            "tags": ["bike_selection"],
        }

        headers = {"Authorization": f"Bearer {GRAFANA_API_KEY}", "Content-Type": "application/json"}
        response = requests.post(GRAFANA_URL, json=grafana_data, headers=headers)

        if response.status_code == 200:
            return {"message": "Bike selection updated in PostgreSQL & Grafana"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update Grafana")

    except Exception as e:
        logging.error(f"🔥 Error storing bike selection: {e}")
        raise HTTPException(status_code=500, detail="Database error")

# ✅ Retrieve All Stored Bike Selections
@app.get("/selections")
async def get_selections():
    """Fetches all bike selections from PostgreSQL."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_name, equipment_id, timestamp FROM bike_selections ORDER BY timestamp DESC;")
                rows = cursor.fetchall()

        return [{"user_name": row[0], "equipment_id": row[1], "timestamp": row[2]} for row in rows]

    except Exception as e:
        logging.error(f"🔥 Error fetching selections: {e}")
        raise HTTPException(status_code=500, detail="Database error")



# ✅ Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

from fastapi import FastAPI
import asyncio
import logging

app = FastAPI()

# Background task reference
ble_scanner_task = None

async def continuous_ble_scanner():
    """Continuously scans for Keiser M3 bikes and processes BLE data."""
    from bleak import BleakScanner
    from keiser_m3_ble_parser import KeiserM3BLEBroadcast  # Ensure this is available

    TARGET_PREFIX = "M3"

    def detection_callback(device, advertisement_data):
        if device.name and device.name.startswith(TARGET_PREFIX):
            try:
                parsed_data = KeiserM3BLEBroadcast(advertisement_data.manufacturer_data[0x0645]).to_dict()
                asyncio.create_task(store_bike_data(parsed_data))
            except Exception as e:
                logging.error(f"⚠️ Error parsing BLE data from {device.name}: {e}")

    scanner = BleakScanner(detection_callback)

    while True:
        logging.info("🔍 Scanning for Keiser M3 bikes...")
        await scanner.start()
        await asyncio.sleep(10)  # Scan duration (10 seconds)
        await scanner.stop()
        logging.info("🔍 Scan cycle completed. Restarting...")

@app.on_event("startup")
async def start_ble_scanner():
    """ Start BLE scanner when FastAPI starts """
    global ble_scanner_task
    ble_scanner_task = asyncio.create_task(continuous_ble_scanner())

@app.on_event("shutdown")
async def stop_ble_scanner():
    """ Stop BLE scanner when FastAPI shuts down """
    global ble_scanner_task
    if ble_scanner_task:
        ble_scanner_task.cancel()
        try:
            await ble_scanner_task
        except asyncio.CancelledError:
            logging.info("🚦 BLE scanner task cancelled cleanly.")
    

# ✅ Start FastAPI Server & Background Scanner
if __name__ == "__main__":
    loop = asyncio.get_event_loop
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
