from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.query_api import QueryApi
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError
from config.config import INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET
import logging
import asyncpg
from datetime import datetime

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

# Save Bike Number and Device Address Mapping
async def save_bike_mapping(bike_number: str, device_address: str) -> bool:
    try:
        conn = await get_timescale_connection()
        query = '''
            INSERT INTO bike_mappings (bike_number, device_address, mapped_at)
            VALUES ($1, $2, NOW())
        '''
        await conn.execute(query, bike_number, device_address)
        await conn.close()
        logger.info(f"✅ Successfully saved bike mapping: {bike_number} -> {device_address}")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving bike mapping: {e}")
        return False

# Get All Bike Mappings
async def get_bike_mappings() -> list:
    try:
        conn = await get_timescale_connection()
        query = '''
            SELECT bike_number, device_address FROM bike_mappings
        '''
        rows = await conn.fetch(query)
        await conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"❌ Error retrieving bike mappings: {e}")
        return []

# Get Latest Bike Data from InfluxDB
def get_latest_bike_data():
    try:
        query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -5m)
            |> filter(fn: (r) => r._measurement == "bike_data")
            |> last()
        '''
        result = query_api.query(org=INFLUXDB_ORG, query=query)
        latest_data = {}
        for table in result:
            for record in table.records:
                bike_id = record.values["bike_id"]
                latest_data[bike_id] = {
                    "distance": record.get_value()
                }
        logger.info("✅ Successfully fetched latest bike data from InfluxDB.")
        return latest_data
    except InfluxDBError as e:
        logger.error(f"❌ Error fetching latest bike data: {e}")
        return {}

# Get Historical Bike Data from TimescaleDB
async def get_historical_data(bike_id: str, start_time: datetime, end_time: datetime) -> list:
    try:
        conn = await get_timescale_connection()
        query = '''
            SELECT * FROM bike_data
            WHERE bike_id = $1
            AND timestamp >= $2
            AND timestamp <= $3
            ORDER BY timestamp ASC
        '''
        rows = await conn.fetch(query, bike_id, start_time, end_time)
        await conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"❌ Error fetching historical bike data: {e}")
        return []
