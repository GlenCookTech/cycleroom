
import pygame
import os
import json
import numpy as np
import asyncio
import httpx
from datetime import datetime
from config.config import (
    SCREEN_WIDTH, 
    SCREEN_HEIGHT, 
    TRACK_WIDTH, 
    TRACK_LENGTH_MILES,
    WAYPOINTS_FILE, 
    BIKE_ICON_PATH, 
    TRACK_IMAGE_PATH
)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Real-Time Bike Race Visualization")
clock = pygame.time.Clock()

# Global Variables
WAYPOINTS = []
BIKE_ICON = None
TRACK_IMAGE = None
bike_data = {}
bike_positions = {}
bike_laps = {}
bike_colors = {}
bike_last_waypoint = {}
font = pygame.font.SysFont(None, 24)

# Assign Colors to Bikes
def assign_bike_colors():
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 165, 0), (255, 255, 0)]
    for i, bike_id in enumerate(bike_data.keys()):
        bike_colors[bike_id] = colors[i % len(colors)]

# Load Assets
def load_assets():
    global WAYPOINTS, BIKE_ICON, TRACK_IMAGE
    # Load Waypoints
    try:
        with open(WAYPOINTS_FILE, "r") as f:
            WAYPOINTS = [(x, y) for x, y in json.load(f)]
        print(f"✅ Loaded {len(WAYPOINTS)} waypoints.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading waypoints: {e}")
        WAYPOINTS = []
    
    # Load Bike Icon
    try:
        BIKE_ICON = pygame.image.load(BIKE_ICON_PATH)
        BIKE_ICON = pygame.transform.scale(BIKE_ICON, (20, 10))
    except pygame.error as e:
        print(f"❌ Error loading bike icon: {e}")
        BIKE_ICON = None
    
    # Load Track Image
    try:
        TRACK_IMAGE = pygame.image.load(TRACK_IMAGE_PATH)
        TRACK_IMAGE = pygame.transform.scale(TRACK_IMAGE, (TRACK_WIDTH, SCREEN_HEIGHT))
    except pygame.error as e:
        print(f"❌ Error loading track image: {e}")
        TRACK_IMAGE = None

# Get bike position with interpolation
def interpolate_position(start_pos, end_pos, progress):
    return (
        int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress),
        int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)
    )

def get_bike_position(distance_miles, bike_id):
    if not WAYPOINTS:
        return (0, 0)

    distance_pixels = (distance_miles / TRACK_LENGTH_MILES) * len(WAYPOINTS)
    index = int(distance_pixels) % len(WAYPOINTS)
    next_index = (index + 1) % len(WAYPOINTS)

    start_pos = WAYPOINTS[index]
    end_pos = WAYPOINTS[next_index]
    progress = (distance_pixels % 1)

    # Update lap counter
    update_lap_counter(bike_id, index)

    bike_positions[bike_id] = interpolate_position(start_pos, end_pos, progress)
    return bike_positions[bike_id]

# Update Lap Counter
def update_lap_counter(bike_id, current_waypoint):
    if bike_id not in bike_laps:
        bike_laps[bike_id] = 0
        bike_last_waypoint[bike_id] = current_waypoint

    # Check if the bike crossed the start/finish line (first waypoint)
    if bike_last_waypoint[bike_id] > current_waypoint and current_waypoint == 0:
        bike_laps[bike_id] += 1
    
    bike_last_waypoint[bike_id] = current_waypoint

# Draw Bike Icons with Smooth Animation
def draw_bike_icons():
    for bike_id, metrics in bike_data.items():
        bike_pos = get_bike_position(metrics["trip_distance"], bike_id)
        color = bike_colors.get(bike_id, (255, 255, 255))
        if BIKE_ICON:
            screen.blit(BIKE_ICON, bike_pos)
            draw_metrics(bike_id, bike_pos, color)

# Draw Real-Time Metrics
def draw_metrics(bike_id, bike_pos, color):
    metrics = bike_data[bike_id]
    y_offset = 15  # Offset for text placement
    text_lines = [
        f"Speed: {metrics['speed']} mph",
        f"Cadence: {metrics['cadence']} rpm",
        f"Power: {metrics['power']} W",
        f"Distance: {metrics['trip_distance']} miles",
        f"Gear: {metrics['gear']}",
        f"Laps: {bike_laps.get(bike_id, 0)}"
    ]
    for line in text_lines:
        text_surface = font.render(line, True, color)
        screen.blit(text_surface, (bike_pos[0] + 25, bike_pos[1] + y_offset))
        y_offset += 15

# Draw Real-Time Leaderboard
def draw_leaderboard():
    sorted_bikes = sorted(bike_data.items(), key=lambda x: x[1]['trip_distance'], reverse=True)
    leaderboard_pos = (TRACK_WIDTH + 50, 50)
    y_offset = 0

    title_surface = font.render("Leaderboard", True, (255, 255, 255))
    screen.blit(title_surface, leaderboard_pos)

    for rank, (bike_id, metrics) in enumerate(sorted_bikes, start=1):
        color = bike_colors.get(bike_id, (255, 255, 255))
        leaderboard_text = f"{rank}. {bike_id}: {metrics['trip_distance']} miles | Laps: {bike_laps.get(bike_id, 0)}"
        text_surface = font.render(leaderboard_text, True, color)
        screen.blit(text_surface, (leaderboard_pos[0], leaderboard_pos[1] + 25 + y_offset))
        y_offset += 25

# Update Display
def update_display():
    screen.fill((0, 0, 0))
    if TRACK_IMAGE:
        screen.blit(TRACK_IMAGE, (0, 0))
    draw_bike_icons()
    draw_leaderboard()
    pygame.display.flip()
    clock.tick(30)  # Maintain 30 FPS

# Fetch Real-Time Data from FastAPI
async def fetch_real_time_data():
    global bike_data
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://127.0.0.1:8000/api/bikes")
            if response.status_code == 200:
                bike_data = response.json()
                assign_bike_colors()
            else:
                print(f"❌ Error fetching real-time data: {response.status_code}")
        except httpx.RequestError as e:
            print(f"❌ HTTP Request Error: {e}")

# Main Loop
async def main_loop():
    load_assets()
    while True:
        await fetch_real_time_data()
        update_display()
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main_loop())
