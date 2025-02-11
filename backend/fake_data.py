import random
import math
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

    # 🚴‍♂️ Simulate Warm-up
    if elapsed_time < 300:
        rider_state["power"] += random.randint(-5, 10)
        rider_state["cadence"] += random.randint(-2, 5)
    # 🚀 Simulate Steady Ride
    elif elapsed_time < 1800:
        rider_state["power"] += random.randint(-10, 10)
        rider_state["cadence"] += random.randint(-3, 3)
    # 🏁 Simulate Cooldown
    else:
        rider_state["power"] -= random.randint(5, 15)
        rider_state["cadence"] -= random.randint(3, 8)

    # ✅ Boundaries for realistic values
    rider_state["power"] = max(50, min(300, rider_state["power"]))
    rider_state["cadence"] = max(60, min(110, rider_state["cadence"]))

    # ❤️ Simulate Heart Rate
    rider_state["heart_rate"] = min(
        190,
        max(100, rider_state["heart_rate"] + math.ceil(rider_state["power"] / 50) + random.randint(-2, 5))
    )

    # 🔧 Adjust Gear Based on Cadence
    if rider_state["cadence"] > 95:
        rider_state["gear"] = min(24, rider_state["gear"] + 1)
    elif rider_state["cadence"] < 75:
        rider_state["gear"] = max(1, rider_state["gear"] - 1)

    # 🔥 Calories Calculation
    rider_state["calories"] += round((rider_state["power"] * 0.00024), 2)

    return {
        "device": "F5:FC:73:B9:9E:CA",
        "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        "power": rider_state["power"],
        "cadence": rider_state["cadence"],
        "heart_rate": rider_state["heart_rate"],
        "gear": rider_state["gear"],
        "calories": round(rider_state["calories"], 2),
    }
