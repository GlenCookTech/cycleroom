import os
import json
import redis
import asyncio
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Load .env file
load_dotenv(dotenv_path="./backend/.env")

# Environment Variables
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

# Initialize FastAPI
app = FastAPI()

# Initialize Redis for caching
redis_client = redis.Redis(host="localhost", port=6379, db=0)

# InfluxDB Client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()


### ✅ **Optimized InfluxDB Query**
async def fetch_gear_data():
    """Fetch max, min, and latest gear values from InfluxDB"""
    query = f"""
    gear_data = from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r["_measurement"] == "gear_data")
      |> filter(fn: (r) => r["_field"] == "gear")

    max_gear = gear_data |> max()
    min_gear = gear_data |> min()
    latest_gear = gear_data |> sort(columns: ["_time"], desc: true) |> limit(n: 1)

    union(tables: [max_gear, min_gear, latest_gear])
    """

    result = query_api.query(query)

    gear_values = {"max": None, "min": None, "current": None}
    for table in result:
        for record in table.records:
            if record.get_field() == "gear":
                value = record.get_value()
                if gear_values["max"] is None or value > gear_values["max"]:
                    gear_values["max"] = value
                if gear_values["min"] is None or value < gear_values["min"]:
                    gear_values["min"] = value
                if gear_values["current"] is None:
                    gear_values["current"] = value

    return gear_values


### ✅ **API Endpoint with Caching**
@app.get("/gear")
async def get_gear_data():
    """Get gear data from InfluxDB with caching"""
    cache_key = "gear_data"
    
    # Check Redis cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # Fetch from InfluxDB if not in cache
    gear_data = await fetch_gear_data()
    redis_client.set(cache_key, json.dumps(gear_data), ex=300)  # Cache for 5 min
    return gear_data


### ✅ **Health Check for Load Balancers**
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}


### ✅ **Run Uvicorn with Performance Optimizations**
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, workers=4)
