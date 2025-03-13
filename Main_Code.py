#pad met finish, aruco code detectie, 2 laps and finish text
import cv2
import numpy as np
import time
import cv2.aruco as aruco

print(cv2.__version__)

# Open de video feed van de camera
cap = cv2.VideoCapture(0)

# Camera instellingen
cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
cap.set(cv2.CAP_PROP_SATURATION, 0.5)

# Definieer het ArUco dictionary en de parameters voor detectie
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()

# Definieer het pad voor de baan (als een lijst van punten)
path_points = [
    (100, 100), (150, 50), (250, 50), (350, 125), (450, 100), (500, 100), (550, 200),  # Top helft van de baan
    (550, 300), (500, 400), (450, 400), (350, 350), (250, 350), (150, 300),   # Onder helft van de baan
    (75, 150), (100, 100)  # Sluit het pad af bij het beginpunt (finishlijn)
]

# Functie om het pad breder te maken
def expand_path(path_points, width=20):
    expanded_points = []
    for i in range(len(path_points) - 1):
        p1, p2 = path_points[i], path_points[i + 1]
        
        # Bereken de vector van p1 naar p2
        vector = np.array(p2) - np.array(p1)
        norm = np.linalg.norm(vector)

        # Vermijd deling door nul
        if norm > 0:
            unit_vector = vector / norm  # Normalizeer de vector
        else:
            unit_vector = np.array([0, 0])  # Zet de unit_vector naar (0, 0)
        
        # Draai de vector 90 graden om de perpendiculaire richting te krijgen
        perpendicular = np.array([-unit_vector[1], unit_vector[0]])
        
        # Verschuif de punten langs de perpendiculaire richting om een breder pad te creëren
        p1_left = tuple((p1 + perpendicular * width / 2).astype(int))
        p1_right = tuple((p1 - perpendicular * width / 2).astype(int))
        p2_left = tuple((p2 + perpendicular * width / 2).astype(int))
        p2_right = tuple((p2 - perpendicular * width / 2).astype(int))

        expanded_points.append([p1_left, p2_left, p2_right, p1_right])

    return expanded_points

# Maak het pad breder
expanded_path = expand_path(path_points, width=5)  # Stel de gewenste breedte hier in

# Variabelen voor ronde detectie
lap_completed = False
lap_start_time = 0
lap_count = 0  # Aantal voltooide ronden
cooldown_time = 2  # Cooldown tijd om meerdere ronde tellingen te voorkomen
last_lap_time = 0  # Tijd van de laatste ronde detectie
lap_text_start_time = 0
lap_text_duration = 2  # Duur om de "Lap Complete" tekst weer te geven

# Definieer de finishlijn (bijvoorbeeld x: 175 tot 225, y: 0 tot 100)
finish_zone = ((175, 0), (225, 100))

# Loop voor het vastleggen van frames
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Detecteer ArUco markers
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    # Teken de ArUco markers op het frame
    aruco.drawDetectedMarkers(frame, corners, ids)

    # Pad tekenen
    for points in expanded_path:
        cv2.fillPoly(frame, [np.array(points)], (0, 0, 255))  # Rood breder pad

    # Controleer of een marker zich binnen de finishzone bevindt
    if ids is not None:
        for corner, marker_id in zip(corners, ids):
            # Het midden van de marker berekenen
            center = np.mean(corner[0], axis=0)
            
            # Controleer of de marker binnen de finishzone valt
            if (finish_zone[0][0] <= center[0] <= finish_zone[1][0]) and (finish_zone[0][1] <= center[1] <= finish_zone[1][1]):
                current_time = time.time()
                if current_time - last_lap_time > cooldown_time:
                    lap_completed = True
                    last_lap_time = current_time

    # Display "Lap Complete" nadat de auto de finishlijn heeft gepasseerd
    if lap_completed:
        lap_count += 1
        lap_completed = False
        lap_text_start_time = time.time()

    if time.time() - lap_text_start_time < lap_text_duration and lap_count < 3:
        cv2.putText(frame, "Lap Complete", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Display "Finished!" als 3 ronden zijn voltooid
    if lap_count >= 3:
        cv2.putText(frame, "Finished!", (150, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

    # Toon het frame met het getrackte object en het pad
    cv2.imshow('Car Tracking with ArUco and Oval Track', frame)

    # Stop de loop bij het indrukken van de 'q' toets
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release de video capture object en sluit alle vensters
cap.release()
cv2.destroyAllWindows()
