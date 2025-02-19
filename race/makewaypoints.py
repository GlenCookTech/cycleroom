import cv2
import numpy as np
import json

# Load the track image
image_path = "race/track.jpg"
try:
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"❌ Unable to load image at {image_path}")
except Exception as e:
    print(e)
    exit()

# Apply thresholding to isolate the track
_, binary = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY_INV)

# Find contours (detects the outer boundary of the track)
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if not contours:
    print("❌ No track contour detected!")
    exit()

# Get the largest contour (assumed to be the track boundary)
track_contour = max(contours, key=cv2.contourArea)

# Compute the track's centerline by applying morphological thinning
skeleton = cv2.ximgproc.thinning(binary)

# Extract centerline waypoints
waypoints = np.column_stack(np.where(skeleton > 0))  # Get all pixels in the skeleton
waypoints = [(int(x), int(y)) for y, x in waypoints]  # Convert to (x, y) format

# Save waypoints to a JSON file
waypoints_json_path = "race/waypoints.json"
try:
    with open(waypoints_json_path, "w") as f:
        json.dump(waypoints, f)
    print(f"✅ Extracted {len(waypoints)} centerline waypoints and saved to {waypoints_json_path}")
except Exception as e:
    print(f"❌ Failed to save waypoints to {waypoints_json_path}: {e}")
