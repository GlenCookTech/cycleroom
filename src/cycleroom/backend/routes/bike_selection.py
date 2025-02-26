
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
import asyncpg
import os

router = APIRouter()

# Database Connection Settings
TIMESCALEDB_HOST = os.getenv("TIMESCALEDB_HOST", "timescaledb")
TIMESCALEDB_USER = os.getenv("POSTGRES_USER", "timescale_user")
TIMESCALEDB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "timescale_password")
TIMESCALEDB_DB = os.getenv("POSTGRES_DB", "timescale_db")

# Pydantic Models
class BikeSelection(BaseModel):
    bike_number: str
    device_address: str

class BikeSelectionResponse(BaseModel):
    bike_number: str
    device_address: str
    date: datetime

# Get TimescaleDB Connection
async def get_timescale_connection():
    conn = await asyncpg.connect(
        user=TIMESCALEDB_USER,
        password=TIMESCALEDB_PASSWORD,
        database=TIMESCALEDB_DB,
        host=TIMESCALEDB_HOST
    )
    return conn

# Save Bike Selection
@router.post("/api/bike-selection", tags=["Bike Selection"], response_model=BikeSelectionResponse)
async def save_bike_selection(selection: BikeSelection):
    conn = await get_timescale_connection()
    query = '''
        INSERT INTO bike_selection (bike_number, device_address, date)
        VALUES ($1, $2, NOW())
        RETURNING bike_number, device_address, date
    '''
    row = await conn.fetchrow(query, selection.bike_number, selection.device_address)
    await conn.close()
    if row:
        return dict(row)
    else:
        raise HTTPException(status_code=500, detail="Failed to save bike selection.")

# Get Bike Selection Mappings
@router.get("/api/bike-selection", tags=["Bike Selection"], response_model=Dict[str, str])
async def get_bike_selection():
    conn = await get_timescale_connection()
    query = '''
        SELECT bike_number, device_address FROM bike_selection ORDER BY date DESC
    '''
    rows = await conn.fetch(query)
    await conn.close()
    return {row["bike_number"]: row["device_address"] for row in rows}
