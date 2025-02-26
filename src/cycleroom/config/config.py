
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "default_token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "default_org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "default_bucket")
QUERY_INTERVAL = int(os.getenv("QUERY_INTERVAL", 2))

# Pygame and Visualization Configuration
SCREEN_WIDTH = int(os.getenv("SCREEN_WIDTH", 1200))
SCREEN_HEIGHT = int(os.getenv("SCREEN_HEIGHT", 600))
TRACK_WIDTH = int(os.getenv("TRACK_WIDTH", 800))
TRACK_LENGTH_MILES = float(os.getenv("TRACK_LENGTH_MILES", 3.0))

# Asset Paths
WAYPOINTS_FILE = os.getenv("WAYPOINTS_FILE", "assets/waypoints.json")
BIKE_ICON_PATH = os.getenv("BIKE_ICON_PATH", "assets/bike_icon.png")
TRACK_IMAGE_PATH = os.getenv("TRACK_IMAGE_PATH", "assets/track.jpg")
