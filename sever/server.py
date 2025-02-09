import asyncio
import json
import sqlite3
import csv
from datetime import datetime
from fastapi import FastAPI, WebSocket, Response
from fastapi.responses import FileResponse
from bleak import BleakScanner, BleakClient

app = FastAPI()

# Store connected WebSockets
connected_clients = set()

# Keiser M Series UUIDs
KEISER_CHARACTERISTIC_UUID = "6e40fff3-b5a3-f393-e0a9-e50e24dcca9e"

# Database Setup
DB_FILE = "keiser_sessions.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT,
            timestamp TEXT,
            power INTEGER,
            cadence INTEGER,
            heart_rate INTEGER,
            calories REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# WebSocket Connection
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

# Calculate Calories Burned
def calculate_calories(power, duration=1):
    """Estimates calories burned per second based on power output."""
    kcal_per_watt_sec = 0.00024  # Approximate metabolic equivalent conversion
    return round(power * kcal_per_watt_sec * duration, 2)

# Store session data
def save_session_data(device, data):
    power = data.get("power", 0)
    calories = calculate_calories(power)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO sessions (device, timestamp, power, cadence, heart_rate, calories)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        device,
        datetime.utcnow().isoformat(),
        power,
        data.get("cadence", 0),
        data.get("heart_rate", 0),
        calories
    ))
    conn.commit()
    conn.close()

# Read data from Keiser bikes
async def read_keiser_data(device_address):
    async with BleakClient(device_address) as client:
        if await client.is_connected():
            print(f"Connected to {device_address}")

            async def notification_handler(sender, data):
                parsed_data = json.loads(data.decode())
                print(f"Bike Data ({device_address}): {parsed_data}")

                # Save session data
                save_session_data(device_address, parsed_data)

                # Send real-time leaderboard updates
                leaderboard = get_leaderboard()
                for ws in connected_clients:
                    await ws.send_text(json.dumps({"leaderboard": leaderboard}))

            await client.start_notify(KEISER_CHARACTERISTIC_UUID, notification_handler)
            await asyncio.sleep(30)
            await client.stop_notify(KEISER_CHARACTERISTIC_UUID)

# API: Get Leaderboard
@app.get("/leaderboard")
def get_leaderboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT device, MAX(power) as max_power, MAX(cadence) as max_cadence, SUM(calories) as total_calories
        FROM sessions
        GROUP BY device
        ORDER BY max_power DESC
        LIMIT 10
    """)
    leaderboard = [{"device": row[0], "max_power": row[1], "max_cadence": row[2], "calories": row[3]} for row in c.fetchall()]
    conn.close()
    return leaderboard

# API: Export Sessions as CSV
@app.get("/export")
def export_sessions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM sessions ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()

    filename = "keiser_sessions.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Device", "Timestamp", "Power", "Cadence", "Heart Rate", "Calories"])
        writer.writerows(rows)

    return FileResponse(filename, media_type="text/csv", filename=filename)

# Start BLE Scanner
@app.on_event("startup")
async def startup_event():
    await read_keiser_data("PUT_YOUR_DEVICE_ADDRESS_HERE")

