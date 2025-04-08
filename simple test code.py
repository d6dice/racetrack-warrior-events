import cv2
import numpy as np

# Kies een ArUco-dictionary en maak de detectieparameters aan
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()

# Maak een dictionary om de trail-punten per marker-ID op te slaan
trails = {}

# Stel voor elke marker-ID een kleur in (BGR-formaat)
marker_colors = {
    0: (255, 0, 0),   # Blauw voor marker-id 0
    1: (0, 255, 0)    # Groen voor marker-id 1
}
default_color = (0, 0, 0)  # Fallbackkleur

# Open de standaard webcam (pas de index aan als dat nodig is)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Kan de camera niet openen!")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Kan frame niet lezen!")
        break

    # Converteer het frame naar grijswaarden voor de detectie
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detecteer ArUco-markers
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    # Als er markers gedetecteerd zijn, werk dan elke marker afzonderlijk af
    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        for idx, marker_id in enumerate(ids.flatten()):
            # Haal de hoekpunten op voor de marker
            marker_corners = corners[idx][0]  # 4 hoekpunten, in een array van vorm (4, 2)
            # Bereken het centrum van de marker
            center_x = int(np.mean(marker_corners[:, 0]))
            center_y = int(np.mean(marker_corners[:, 1]))
            
            # Voeg het centrum toe aan de trail voor deze marker-ID
            if marker_id not in trails:
                trails[marker_id] = []
            trails[marker_id].append((center_x, center_y))

    # Teken de trail voor elk marker-ID afzonderlijk
    for marker_id, points in trails.items():
        if len(points) > 1:
            # Gebruik de kleur die is ingesteld voor deze marker-ID, of gebruik de default kleur
            color = marker_colors.get(marker_id, default_color)
            pts = np.array(points, dtype=np.int32)
            cv2.polylines(frame, [pts], isClosed=False, color=color, thickness=2)

    # Toon het frame met de trails
    cv2.imshow("ArUco Marker Trails", frame)
    
    # Druk op 'q' om te stoppen
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
