
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.query_api import QueryApi
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError
from config.config import INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET
import logging
import asyncpg
import asyncio

logger = logging.getLogger(__name__)

# Initialize InfluxDB Client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()
write_api = client.write_api(write_options=SYNCHRONOUS)

# Asynchronous TimescaleDB Connection
async def get_timescale_connection():
    conn = await asyncpg.connect(
        user='timescale_user', 
        password='timescale_password',
        database='timescale_db',
        host='timescaledb_host'
    )
    return conn

# Write real-time BLE data to InfluxDB
def write_ble_data_to_influx(bike_id, data):
    try:
        point = (
            Point("bike_data")
            .tag("bike_id", bike_id)
            .field("cadence", data.get("cadence", 0))
            .field("heart_rate", data.get("heart_rate", 0))
            .field("power", data.get("power", 0))
            .field("trip_distance", data.get("trip_distance", 0))
            .field("gear", data.get("gear", 0))
        )
        write_api.write(bucket=INFLUXDB_BUCKET, record=point)
        logger.info(f"✅ Successfully written data to InfluxDB for bike {bike_id}")
    except InfluxDBError as e:
        logger.error(f"❌ Error writing data to InfluxDB: {e}")

# Write historical data to TimescaleDB
async def write_ble_data_to_timescale(bike_id, data):
    try:
        conn = await get_timescale_connection()
        query = '''
            INSERT INTO bike_data (bike_id, cadence, heart_rate, power, trip_distance, gear, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
        '''
        await conn.execute(
            query, 
            bike_id, 
            data.get("cadence", 0), 
            data.get("heart_rate", 0), 
            data.get("power", 0), 
            data.get("trip_distance", 0), 
            data.get("gear", 0)
        )
        await conn.close()
        logger.info(f"✅ Successfully written data to TimescaleDB for bike {bike_id}")
    except Exception as e:
        logger.error(f"❌ Error writing data to TimescaleDB: {e}")

# Retrieve historical data from TimescaleDB
async def get_historical_data(bike_id, start_time, end_time):
    try:
        conn = await get_timescale_connection()
        query = '''
            SELECT * FROM bike_data 
            WHERE bike_id = $1 AND timestamp BETWEEN $2 AND $3
            ORDER BY timestamp ASC
        '''
        rows = await conn.fetch(query, bike_id, start_time, end_time)
        await conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"❌ Error retrieving historical data: {e}")
        return []
