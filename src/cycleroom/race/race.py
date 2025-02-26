import pygame
import os
import json
import cv2
import numpy as np
import math
import threading
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
from flask import Flask, Response
import time


# Initialize Pygame
pygame.init()

# Init InfluxDB
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()

# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 600
TRACK_WIDTH = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bike Race Visualization")

# Load the track image
try:
    TRACK_IMAGE = pygame.image.load("assets/track.jpg")
    TRACK_IMAGE = pygame.transform.scale(TRACK_IMAGE, (TRACK_WIDTH, SCREEN_HEIGHT))
except pygame.error as e:
    print(f"❌ Error loading track image: {e}")
    TRACK_IMAGE = None

# Load waypoints
WAYPOINTS_FILE = "assets/waypoints.json"
try:
    with open(WAYPOINTS_FILE, "r") as f:
        WAYPOINTS = [(x, y) for x, y in json.load(f)]
    print(f"✅ Loaded {len(WAYPOINTS)} waypoints.")
except FileNotFoundError:
    print("❌ Waypoints file not found!")
    WAYPOINTS = []

# Load bike icon
try:
    BIKE_ICON = pygame.image.load("assets/bike_icon.png")
    BIKE_ICON = pygame.transform.scale(BIKE_ICON, (20, 10))
except pygame.error as e:
    print(f"❌ Error loading bike icon: {e}")
    BIKE_ICON = None

# Colors
BIKE_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0)]
FONT = pygame.font.Font(None, 36)  # Increased font size

# Get bike position based on distance
def get_bike_position(distance_miles):
    if not WAYPOINTS:
        return (0, 0)
    
    track_length_miles = 3.0  
    distance_pixels = (distance_miles / track_length_miles) * len(WAYPOINTS)
    index = int(distance_pixels) % len(WAYPOINTS)
    
    if index < 0 or index >= len(WAYPOINTS):
        return (0, 0)

    # Get the waypoint coordinates
    x, y = WAYPOINTS[index]

    # Adjust the bike position to fit the screen and align with the track image
    x = int(200 + (x * (TRACK_WIDTH / 1000)))
    y = int(y * (SCREEN_HEIGHT / 500))
    
    # Debugging: Print the calculated positions
    print(f"Bike Position - X: {x}, Y: {y}")

    return (x, y)


# Fetch race data (distance, gear, power)
def get_race_data():
    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -30s)
            |> filter(fn: (r) => r["_measurement"] == "keiser_m3")
            |> filter(fn: (r) => r["_field"] == "distance" or r["_field"] == "gear" or r["_field"] == "power")
            |> last()
    '''
    tables = query_api.query(query)
    
    bike_data = {}
    
    for table in tables:
        for record in table.records:
            equipment_id = record.values.get("equipment_id", f"bike_{len(bike_data)}")
            field = record.values["_field"]
            value = record.get_value()
            
            if equipment_id not in bike_data:
                bike_data[equipment_id] = {"distance": 0.0, "gear": 0, "power": 0}
            
            if value is not None:
                bike_data[equipment_id][field] = value
    
    return bike_data

# Flask server for video streaming
app = Flask(__name__)

def pygame_to_frame(surface):
    frame = pygame.surfarray.array3d(surface)
    frame = np.transpose(frame, (1, 0, 2))
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return frame

def generate_frames():
    while True:
        frame = pygame_to_frame(screen)
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Add a short delay to control the frame rate
        time.sleep(0.03)  # Approximately 30 FPS

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



# Game Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear screen
    screen.fill((0, 0, 0))  # Fill screen with black
    
    # Draw track
    if TRACK_IMAGE:
        screen.blit(TRACK_IMAGE, (200, 0))
    
    # Draw waypoints
    for point in WAYPOINTS:
        pygame.draw.circle(screen, (255, 255, 255), point, 3)
    
     # Draw bikes
    bike_data = get_race_data()
    for i, (bike_id, data) in enumerate(bike_data.items()):
        pos = get_bike_position(data["distance"])
        color = BIKE_COLORS[i % len(BIKE_COLORS)]
        
        # Check if the position is valid before drawing
        if pos != (0, 0) and pos[0] > 0 and pos[1] > 0:
            # Draw bike as a colored circle if no icon is available
            pygame.draw.circle(screen, color, pos, 10)
            
            # Display bike information with bigger and black font
            text = FONT.render(f"{bike_id} - Gear: {data['gear']} Power: {data['power']}", True, (0, 0, 0))
            screen.blit(text, (pos[0] + 20, pos[1] - 20))
        else:
            print(f"Invalid position for {bike_id}: {pos}")

    
    # Update display
    pygame.display.flip()

pygame.quit()
