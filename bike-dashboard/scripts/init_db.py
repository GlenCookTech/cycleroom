import sqlite3

# Connect to SQLite database (or create if it doesn't exist)
conn = sqlite3.connect("mapping.db")
cursor = conn.cursor()

# Create the bike assignment table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS bike_assignments (
        bike_id TEXT PRIMARY KEY,
        user_name TEXT
    )
""")

# Insert sample data
bike_data = [
    ("bike_001", "John Doe"),
    ("bike_002", "Alice Smith"),
    ("bike_003", "Mike Johnson"),
]

cursor.executemany("INSERT OR IGNORE INTO bike_assignments (bike_id, user_name) VALUES (?, ?)", bike_data)

# Commit and close
conn.commit()
conn.close()

print("✅ SQLite database initialized with sample bike-user mappings.")
