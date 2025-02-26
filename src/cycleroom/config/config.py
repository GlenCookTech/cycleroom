from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

INFLUXDB_URL = os.getenv('INFLUXDB_URL')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET')

TIMESCALE_HOST = os.getenv("TIMESCALE_HOST")
TIMESCALE_DB = os.getenv("TIMESCALE_DB")
TIMESCALE_USER = os.getenv("TIMESCALE_USER")
TIMESCALE_PASSWORD = os.getenv("TIMESCALE_PASSWORD")
TIMESCALE_PORT = os.getenv("TIMESCALE_PORT")


GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000/api/annotations")
GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY", "your-api-key")