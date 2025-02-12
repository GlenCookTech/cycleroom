import os
import json
import asyncio
import uvicorn
import psycopg2
from fake_data import generate_realistic_data
from ble_listener import scan_keiser_bikes
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

# Load environment variables
load_dotenv()
TIMESCALE_HOST = os.getenv("TIMESCALE_HOST", "localhost")
TIMESCALE_DB = os.getenv("TIMESCALE_DB", "cycleroom")
TIMESCALE_USER = os.getenv("TIMESCALE_USER", "postgres")
TIMESCALE_PASSWORD = os.getenv("TIMESCALE_PASSWORD", "password")
TIMESCALE_PORT = os.getenv("TIMESCALE_PORT", "5432")

# Connect to TimescaleDB
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
    return psycopg2.connect(
        host=TIMESCALE_HOST,
        database=TIMESCALE_DB,
        user=TIMESCALE_USER,
        password=TIMESCALE_PASSWORD,
        port=TIMESCALE_PORT
    )

# Initialize FastAPI
app = FastAPI()

# Configure CORS to allow WebSocket connections from Grafana
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections storage
active_connections = {}

# Create Table for TimescaleDB
def create_timescale_table():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keiser_m3 (
                    time TIMESTAMPTZ NOT NULL,
                    equipment_id TEXT,
                    power INT,
                    cadence INT,
                    heart_rate INT,
                    gear INT,
                    caloric_burn INT,
                    duration_minutes INT,
                    duration_seconds INT,
                    distance INT
                );
            """)
            cursor.execute("SELECT create_hypertable('keiser_m3', 'time', if_not_exists => TRUE);")
            conn.commit()
create_timescale_table()

# Store session data in TimescaleDB
@app.post("/sessions")
async def create_session(data: dict):
    print("📥 Incoming request data:", json.dumps(data, indent=2))  # Log incoming request

    required_keys = ["equipment_id", "timestamp", "power", "gear", "distance", "cadence", "heart_rate", "caloric_burn", "duration_minutes", "duration_seconds"]
    if not all(key in data for key in required_keys):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        timestamp = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        # Explicitly cast values to match TimescaleDB column types
        equipment_id = str(data["equipment_id"])
        power = int(data["power"])
        cadence = int(data["cadence"])
        heart_rate = int(data["heart_rate"])
        gear = int(data["gear"])
        caloric_burn = int(data["caloric_burn"])
        duration_minutes = int(data["duration_minutes"])
        duration_seconds = int(data["duration_seconds"])
        distance = int(data["distance"])
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = (
                    "INSERT INTO keiser_m3 (time, equipment_id, power, cadence, heart_rate, gear, caloric_burn, "
                    "duration_minutes, duration_seconds, distance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                )
                values = (timestamp, equipment_id, power, cadence, heart_rate, gear, caloric_burn, duration_minutes, duration_seconds, distance)
                
                print("🔹 Preparing to execute query:")
                print("   Query:", query)
                print("   Values:", values)
                print("   Value types:", [type(v) for v in values])
                
                try:
                    cursor.execute(query, values)
                    conn.commit()
                    print("✅ Insert committed successfully.")
                    
                    # Check if row was inserted
                    if cursor.rowcount == 0:
                        print("⚠️ No rows were inserted! Rolling back.")
                        conn.rollback()
                    else:
                        print(f"✅ {cursor.rowcount} row(s) inserted.")
                    
                    # Verify data was inserted
                    cursor.execute("SELECT * FROM keiser_m3 ORDER BY time DESC LIMIT 1;")
                    inserted_data = cursor.fetchone()
                    print(f"🔍 Last inserted row: {inserted_data}")
                except psycopg2.Error as db_error:
                    conn.rollback()
                    print(f"🔥 SQL Execution Error: {db_error.pgcode} - {db_error.pgerror}")
                    raise HTTPException(status_code=500, detail=f"SQL Error: {db_error.pgcode} - {db_error.pgerror}")

        await broadcast_ws(data)
    except Exception as e:
        print(f"🔥 General Error Writing to TimescaleDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Session saved successfully", "data": data}

# WebSocket Endpoint for Real-Time Streaming per Equipment
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
        active_connections[equipment_id].remove(websocket)
        if not active_connections[equipment_id]:
            del active_connections[equipment_id]

# Broadcast updates to WebSocket clients per Equipment
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

# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Start FastAPI Server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
