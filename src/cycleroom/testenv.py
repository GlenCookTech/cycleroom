from dotenv import load_dotenv
import os

# Get absolute path to the .env file
dotenv_path = os.path.abspath("config/.env")

# Load environment variables
dotenv_loaded = load_dotenv(dotenv_path=dotenv_path)

print(f"otenv_path: {dotenv_path}")

print(f".env loaded: {dotenv_loaded}")
print(f"INFLUXDB_URL: {os.environ.get('INFLUXDB_URL', 'Not Set')}")
