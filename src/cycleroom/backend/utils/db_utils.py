
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.query_api import QueryApi
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError
from config.config import INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET
import logging
import asyncpg

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
