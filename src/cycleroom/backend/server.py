
from fastapi import FastAPI
from backend.routes.bike_data import router as bike_data_router
from backend.routes.historical_data import router as historical_data_router
import logging

# Logger Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI App Initialization
app = FastAPI(
    title="CycleRoom API",
    description="API for real-time and historical bike race data",
    version="1.0.0"
)

# Register Modular Routers
app.include_router(bike_data_router)
app.include_router(historical_data_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "CycleRoom API is running!"}
