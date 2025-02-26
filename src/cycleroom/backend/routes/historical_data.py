
from fastapi import APIRouter, HTTPException, Query
from backend.utils.db_utils import get_historical_data
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# Response Model for Historical Data
class HistoricalDataItem(BaseModel):
    bike_id: str
    cadence: int
    heart_rate: int
    power: int
    trip_distance: float
    gear: int
    timestamp: datetime

@router.get("/api/historical", tags=["Historical Data"], response_model=List[HistoricalDataItem])
async def get_historical(
    bike_id: str, 
    start_time: Optional[str] = Query(None, description="Start time in ISO format (e.g., 2023-01-01T00:00:00Z)"),
    end_time: Optional[str] = Query(None, description="End time in ISO format (e.g., 2023-01-01T23:59:59Z)")
):
    '''
    Retrieve historical bike data from TimescaleDB.
    '''
    # Validate time inputs
    try:
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (e.g., 2023-01-01T00:00:00Z)")
    
    # Query historical data
    data = await get_historical_data(bike_id, start, end)
    if not data:
        raise HTTPException(status_code=404, detail="No historical data found for the given criteria.")
    
    return data
