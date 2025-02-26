from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="cycleroom/config/.env")

print(os.environ.get("INFLUXDB_URL"))  # Should print the expected value
