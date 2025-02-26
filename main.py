"""
Main entry point for Cycleroom.
Starts the FastAPI server from server.py.
"""

import uvicorn
import multiprocessing
from dotenv import load_dotenv
import backend.ble_listener
import os

# Load environment variables
load_dotenv(dotenv_path="/home/glen/github/cycleroom/config/.env ")

# Debug: Print InfluxDB variables
influx_vars = ["INFLUXDB_URL", "INFLUXDB_TOKEN", "INFLUXDB_ORG", "INFLUXDB_BUCKET"]
for var in influx_vars:
    print(f"{var}: {os.environ.get(var, 'Not Set')}")
    
def start_server():
    """Starts the FastAPI server."""
    print("🚀 Starting Cycleroom FastAPI server...")
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)

def start_race():
    """Starts the Race Dashboard."""
    print("🚀🚦 Starting the Race Dashboard")
    uvicorn.run("race.race:app", host="0.0.0.0", port=8001, reload=True)

def start_blescanner():
    """Starts the BLE Scanner."""
    print("🚀🚦 Starting the BLE Scanner")
    uvicorn.run("backend.ble_listener:app", host="0.0.0.0", port=8002, reload=True)

if __name__ == "__main__":
    server_process = multiprocessing.Process(target=start_server)
    race_process = multiprocessing.Process(target=start_race)
    blescanner_process = multiprocessing.Process(target=start_blescanner)
    
    server_process.start()
    race_process.start()
    blescanner_process.start()

    server_process.join()
    race_process.join()
    blescanner_process.join()