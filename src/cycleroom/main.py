"""
Main entry point for Cycleroom.
Starts the FastAPI server from server.py.
"""

import uvicorn
import multiprocessing

def start_server():
    """Starts the FastAPI server."""
    print("🚀 Starting Cycleroom FastAPI server...")
    uvicorn.run("backend:server:app", host="0.0.0.0", port=8000, reload=True)

def start_race():
    """Starts the Race Dashboard."""
    print("🚀🚦 Starting the Race Dashboard")
    uvicorn.run("race.race:app", host="0.0.0.0", port=8001, reload=True)

def start_blescanner():
    """Starts the BLE Scanner."""
    print("🚀🚦 Starting the BLE Scanner")
    cycleroom.backend.keiser_m3_ble_parser.scan_keiser_bikes()

if __name__ == "__main__":
    server_process = multiprocessing.Process(target=start_server)
    race_process = multiprocessing.Process(target=start_race)

    server_process.start()
    race_process.start()

    server_process.join()
    race_process.join()