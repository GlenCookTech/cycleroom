import pygame
import numpy as np
from scipy.ndimage import sobel
import json

# Load track image
TRACK_IMAGE = pygame.image.load("./race/track.jpg")
TRACK_IMAGE = pygame.transform.scale(TRACK_IMAGE, (1000, 600))
image_array = pygame.surfarray.array3d(TRACK_IMAGE)  # Convert to NumPy array

# Convert to grayscale
gray = np.dot(image_array[..., :3], [0.2989, 0.5870, 0.1140])

# Detect edges using Sobel filter (alternative to OpenCV Canny)
edges_x = sobel(gray, axis=0)
edges_y = sobel(gray, axis=1)
edges = np.hypot(edges_x, edges_y)

# Threshold edges
threshold = np.percentile(edges, 95)  # Keep only strongest edges
edges[edges < threshold] = 0

# Extract waypoints from edge pixels
waypoints = list(zip(*np.where(edges > 0)))  # Get (y, x) pixel locations

# Save waypoints
with open("waypoints.json", "w") as f:
    json.dump(waypoints, f)

print(f"Extracted {len(waypoints)} waypoints and saved to waypoints.json")
