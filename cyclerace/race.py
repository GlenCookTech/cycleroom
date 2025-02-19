import pygame
import random

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bike Race Visualization")

# Load track (placeholder for now - could be an image or drawn track)
TRACK_COLOR = (50, 50, 50)
TRACK_RADIUS = 200
TRACK_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# Bike settings
BIKE_COUNT = 3
BIKE_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
BIKE_RADIUS = 10

# Function to generate bike positions around a circular track
def get_bike_position(distance):
    angle = (distance % 360) * (3.14159 / 180)  # Convert to radians
    x = TRACK_CENTER[0] + TRACK_RADIUS * pygame.math.cos(angle)
    y = TRACK_CENTER[1] + TRACK_RADIUS * pygame.math.sin(angle)
    return int(x), int(y)

# Get realtime race data
def get_race_data():
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -10m)  // Get the last 10 minutes of data
        |> filter(fn: (r) => r["_measurement"] == "bike_race")
        |> filter(fn: (r) => r["_field"] == "distance")
        |> last()
    '''
    tables = query_api.query(query)

    bike_distances = {}
    for table in tables:
        for record in table.records:
            bike_id = record.values["bike_id"]
            bike_distances[bike_id] = record.get_value()
    
    return bike_distances

# Main loop
running = True
clock = pygame.time.Clock()
distances = [0] * BIKE_COUNT  # Initial distances for bikes

while running:
    screen.fill((200, 200, 200))  # Background color
    
    # Draw track
    pygame.draw.circle(screen, TRACK_COLOR, TRACK_CENTER, TRACK_RADIUS, 5)
    
    # Update bike positions (for now, we increment distances randomly)
    for i in range(BIKE_COUNT):
        race_data = get_race_data()
        for i, bike_id in enumerate(race_data.keys()):
            distances[i] = race_data[bike_id]  # Update with real data
        bike_pos = get_bike_position(distances[i])
        pygame.draw.circle(screen, BIKE_COLORS[i], bike_pos, BIKE_RADIUS)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    pygame.display.flip()
    clock.tick(30)  # Limit to 30 FPS

pygame.quit()
