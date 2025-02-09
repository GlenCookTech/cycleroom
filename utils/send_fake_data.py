import math
import time
import random
from datetime import datetime, timezone

# ✅ Simulated Rider State
rider_state = {
    "power": 100,  # Watts
    "cadence": 80,  # RPM
    "heart_rate": 120,  # BPM
    "gear": 10,  # Start in mid-range gear
    "calories": 0.0,
    "session_start": datetime.utcnow(),
}

# ✅ Function to Generate More Realistic Fake Data
def generate_realistic_data():
    elapsed_time = (datetime.utcnow() - rider_state["session_start"]).seconds

    # 🚴‍♂️ Simulate gradual increase in power and cadence (warm-up phase)
    if elapsed_time < 300:  # First 5 minutes
        rider_state["power"] += random.randint(-5, 10)
        rider_state["cadence"] += random.randint(-2, 5)
    # 🚀 Simulate steady riding phase
    elif elapsed_time < 1800:  # First 30 minutes
        rider_state["power"] += random.randint(-10, 10)
        rider_state["cadence"] += random.randint(-3, 3)
    # 🏁 Simulate cooldown phase
    else:
        rider_state["power"] -= random.randint(5, 15)
        rider_state["cadence"] -= random.randint(3, 8)

    # ✅ Boundaries for realistic cycling values
    rider_state["power"] = max(50, min(300, rider_state["power"]))
    rider_state["cadence"] = max(60, min(110, rider_state["cadence"]))

    # ❤️ Heart rate increases with power & cadence but has randomness
    rider_state["heart_rate"] = min(
        190,
        max(100, rider_state["heart_rate"] + math.ceil(rider_state["power"] / 50) + random.randint(-2, 5))
    )

    # 🔧 Gear changes dynamically based on cadence
    if rider_state["cadence"] > 95:
        rider_state["gear"] = min(24, rider_state["gear"] + 1)
    elif rider_state["cadence"] < 75:
        rider_state["gear"] = max(1, rider_state["gear"] - 1)

    # 🔥 Calories burned estimation
    rider_state["calories"] += round((rider_state["power"] * 0.00024), 2)

    # ✅ Return formatted fake session data
    return {
        "device": "F5:FC:73:B9:9E:CA",
        "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        "power": rider_state["power"],
        "cadence": rider_state["cadence"],
        "heart_rate": rider_state["heart_rate"],
        "gear": rider_state["gear"],
        "calories": round(rider_state["calories"], 2),
    }

# ✅ API Route for Simulating Realistic Bike Data
@app.get("/send_fake_data")
def send_fake_data():
    data = generate_realistic_data()
    create_session(data)
    print(f"📡 Sent realistic fake data: {data}")
    return {"message": "Realistic fake data sent", "data": data}

# ✅ Continuous Fake Data Stream (Optional)
def simulate_ride():
    while True:
        send_fake_data()
        time.sleep(5)  # Send data every 5 seconds

# Uncomment below to run continuous fake data generation in the background
# asyncio.create_task(simulate_ride())
# print("🚴‍♂️ Simulated ride started in the background!")