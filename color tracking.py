#tracking car including drawing and finish line

import cv2
import numpy as np
import time

# Open the video feed from OBS Studio (or your camera)
cap = cv2.VideoCapture(2)

# Adjust camera properties to reduce overexposure
cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
cap.set(cv2.CAP_PROP_SATURATION, 0.5)

# Create a window for the trackbars
cv2.namedWindow('HSV Trackbars')

# Create trackbars for adjusting HSV ranges
cv2.createTrackbar('Lower H', 'HSV Trackbars', 26, 179, lambda x: None)
cv2.createTrackbar('Lower S', 'HSV Trackbars', 1, 255, lambda x: None)
cv2.createTrackbar('Lower V', 'HSV Trackbars', 128, 255, lambda x: None)
cv2.createTrackbar('Upper H', 'HSV Trackbars', 69, 179, lambda x: None)
cv2.createTrackbar('Upper S', 'HSV Trackbars', 255, 255, lambda x: None)
cv2.createTrackbar('Upper V', 'HSV Trackbars', 255, 255, lambda x: None)

# Create a list to store previous car positions for drawing the path
car_path = []

# Predefine a more complex track path (an oval track example)
path_points = [
    (100, 100), (150, 50), (250, 50), (350, 150), (350, 150), (450, 100), (500, 100), (600, 200),  # Top half of the oval
    (600, 300), (500, 400), (450, 400), (400, 300), (300, 300), (250, 300), (150, 400), (100, 400), (0, 300),   # Bottom half of the oval
    (0, 150), (100, 100)  # Closing the loop to the start point (finish line)
]

# Function to expand the path to make it wider
def expand_path(path_points, width=20):
    expanded_points = []
    for i in range(len(path_points) - 1):
        p1, p2 = path_points[i], path_points[i + 1]
        
        # Calculate the vector from p1 to p2
        vector = np.array(p2) - np.array(p1)
        norm = np.linalg.norm(vector)

        # Check if the norm is greater than zero to avoid division by zero
        if norm > 0:
            unit_vector = vector / norm  # Normalize the vector
        else:
            unit_vector = np.array([0, 0])  # If norm is zero, set the unit_vector to (0, 0)
        
        # Rotate the vector 90 degrees to get the perpendicular direction
        perpendicular = np.array([-unit_vector[1], unit_vector[0]])
        
        # Shift the points along the perpendicular direction to create a wider path
        p1_left = tuple((p1 + perpendicular * width / 2).astype(int))
        p1_right = tuple((p1 - perpendicular * width / 2).astype(int))
        p2_left = tuple((p2 + perpendicular * width / 2).astype(int))
        p2_right = tuple((p2 - perpendicular * width / 2).astype(int))

        expanded_points.append([p1_left, p2_left, p2_right, p1_right])

    return expanded_points

# Make the path wider
expanded_path = expand_path(path_points, width=50)  # Set the desired width here

# Variables to manage lap detection
lap_completed = False
lap_start_time = 0
lap_count = 0  # To count how many times the lap is completed

# Define the finish line region (x: 175 to 225, y: 0 to 100)
finish_zone = ((175, 0), (225, 100))

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        break
    
    # Draw a grid on the frame every 50 pixels
    height, width, _ = frame.shape
    for x in range(0, width, 50):
        cv2.line(frame, (x, 0), (x, height), (200, 200, 200), 1)
    for y in range(0, height, 50):
        cv2.line(frame, (0, y), (width, y), (200, 200, 200), 1)    

    # Convert the frame to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Get the current positions of the trackbars
    lower_h = cv2.getTrackbarPos('Lower H', 'HSV Trackbars')
    lower_s = cv2.getTrackbarPos('Lower S', 'HSV Trackbars')
    lower_v = cv2.getTrackbarPos('Lower V', 'HSV Trackbars')
    upper_h = cv2.getTrackbarPos('Upper H', 'HSV Trackbars')
    upper_s = cv2.getTrackbarPos('Upper S', 'HSV Trackbars')
    upper_v = cv2.getTrackbarPos('Upper V', 'HSV Trackbars')

    # Define the HSV range for the car color (based on trackbar values)
    lower_car = np.array([lower_h, lower_s, lower_v])
    upper_car = np.array([upper_h, upper_s, upper_v])

    # Create a mask for the car color
    mask = cv2.inRange(hsv, lower_car, upper_car)

    # Apply morphological operations to reduce noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Filter out small contours
        if cv2.contourArea(contour) > 500:
            # Get the bounding box of the contour
            x, y, w, h = cv2.boundingRect(contour)
            # Calculate the center of the bounding box
            center = (x + w // 2, y + h // 2)
            # Add the center point to the car_path list
            car_path.append(center)

            # Draw the bounding box on the original frame
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Check if the car is within the finish zone
            if (finish_zone[0][0] <= center[0] <= finish_zone[1][0]) and (finish_zone[0][1] <= center[1] <= finish_zone[1][1]):
                if not lap_completed:
                    lap_completed = True
                    lap_start_time = time.time()

    # Draw the expanded (wider) path on the frame
    for points in expanded_path:
        cv2.fillPoly(frame, [np.array(points)], (0, 0, 255))  # Red wider path

    # Draw the car's path (lines connecting previous positions)
    for i in range(1, len(car_path)):
        cv2.line(frame, car_path[i - 1], car_path[i], (0, 255, 0), 2)  # Green car path
 
    # Draw a blue thin line from (200, 25) to (200, 75)
    cv2.line(frame, (200, 25), (200, 75), (255, 0, 0), 3)  # Blue line with thickness of 1

    # Display "Lap Complete" after the car crosses the finish zone
    if lap_completed:
        if lap_count < 2:
            cv2.putText(frame, "Lap Complete", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        # If 3 seconds have passed, reset and update lap count
        if time.time() - lap_start_time > 3:
            lap_completed = False
            lap_count += 1

    # Display "Finished!" if 3 laps are completed
    if lap_count >= 3:
        cv2.putText(frame, "Finished!", (150, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

    # Show the original frame with the tracked object and the path
    cv2.imshow('Car Tracking with Oval Track', frame)
    # Show the mask (optional)
    cv2.imshow('Mask', mask)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close all windows
cap.release()
cv2.destroyAllWindows()
