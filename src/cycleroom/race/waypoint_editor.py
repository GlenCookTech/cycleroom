import pygame
import json
import cv2
import numpy as np
import sys
import os

# Load waypoints from file
WAYPOINTS_FILE = "./waypoints.json"
if not os.path.exists(WAYPOINTS_FILE):
    print("❌ Waypoints file not found! Creating a new one.")
    WAYPOINTS = []
    try:
        with open(WAYPOINTS_FILE, "w") as f:
            json.dump(WAYPOINTS, f)
            f.flush()  # Force writing
        print(f"✅ Created new waypoints file at {WAYPOINTS_FILE}")
    except Exception as e:
        print(f"❌ Failed to create waypoints file: {e}")
else:
    try:
        with open(WAYPOINTS_FILE, "r") as f:
            WAYPOINTS = [tuple(x) for x in json.load(f)]  # Convert lists back to tuples
        print(f"✅ Loaded {len(WAYPOINTS)} waypoints for editing.")
    except Exception as e:
        print(f"❌ Failed to load waypoints: {e}")
        WAYPOINTS = []

# Initialize Pygame
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Edit Waypoints")

# Load the track image
TRACK_IMAGE = pygame.image.load("track.jpg")
TRACK_IMAGE = pygame.transform.scale(TRACK_IMAGE, (SCREEN_WIDTH, SCREEN_HEIGHT))

running = True
while running:
    screen.fill((0, 0, 0))
    screen.blit(TRACK_IMAGE, (0, 0))
    
    # Draw waypoints
    for i, point in enumerate(WAYPOINTS):
        pygame.draw.circle(screen, (255, 0, 0), point, 5)
    
    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            WAYPOINTS.append((x, y))
            print(f"🖊️ Added waypoint: {(x, y)}")
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                try:
                    with open(WAYPOINTS_FILE, "w") as f:
                        json.dump([list(p) for p in WAYPOINTS], f)  # Save as lists
                        f.flush()
                    print("💾 Waypoints saved!")
                except Exception as e:
                    print(f"❌ Failed to save waypoints: {e}")
            elif event.key == pygame.K_q:
                running = False  # Quit on 'Q' key

# **Auto-save waypoints before exiting**
try:
    with open(WAYPOINTS_FILE, "w") as f:
        json.dump([list(p) for p in WAYPOINTS], f)  # Save as lists
        f.flush()
    print("✅ Auto-saved waypoints before exit.")
except Exception as e:
    print(f"❌ Failed to auto-save waypoints: {e}")

pygame.quit()

# Function to draw waypoints
def draw_waypoint_connections():
    try:
        track_image = cv2.imread("track.jpg")
        if track_image is None:
            raise FileNotFoundError("❌ Unable to load image at track.jpg")
        track_image = cv2.resize(track_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception as e:
        print(e)
        return

    image = track_image.copy()
    
    # Draw lines between waypoints
    for i in range(len(WAYPOINTS) - 1):
        cv2.line(image, WAYPOINTS[i], WAYPOINTS[i + 1], (0, 255, 0), 2)

    if len(WAYPOINTS) > 1:
        cv2.line(image, WAYPOINTS[-1], WAYPOINTS[0], (0, 255, 0), 2)  # Close the loop

    output_path = "waypoints_connected.jpg"
    
    try:
        cv2.imwrite(output_path, image)
        print(f"📷 Saved connected waypoints image at {output_path}")
        
        # Show the image
        cv2.imshow("Waypoint Connections", image)

        # **Wait for 'Q' key to close**
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        cv2.destroyAllWindows()

    except Exception as e:
        print(f"❌ Failed to save or display waypoints image: {e}")
    finally:
        cv2.destroyAllWindows()
        sys.exit(0)  # Exit the script properly

# Call function **AFTER** Pygame loop ends
draw_waypoint_connections()
