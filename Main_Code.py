#twee auto’s met aruco en afbeelding. Laps en finish worden geregistreerd, lapcounters staan naast het beeld. Reset counters met r. 
import cv2 
import numpy as np
import time
import cv2.aruco as aruco

# Controleer OpenCV-versie
print(f"OpenCV-versie: {cv2.__version__}")

# Open de camera
cap = cv2.VideoCapture(0)

# Laad afbeeldingen met transparantie
def load_image(path, max_width, max_height):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Afbeelding niet gevonden: {path}")
        return None
    h, w = img.shape[:2]
    scale = min(max_width / w, max_height / h) if (w > max_width or h > max_height) else 1
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

green_car = load_image('D:\\werk\\warrior events\\groene_auto.png', 640, 480)
blue_car = load_image('D:\\werk\\warrior events\\blauwe_auto.png', 640, 480)

# Pad tekenen functie
def expand_path(path_points, width=20):
    expanded_points = []
    for i in range(len(path_points) - 1):
        p1, p2 = path_points[i], path_points[i + 1]
        # Bereken de vector van p1 naar p2
        vector = np.array(p2) - np.array(p1)
        norm = np.linalg.norm(vector)
        
        if norm > 0:
            unit_vector = vector / norm
        else:
            unit_vector = np.array([0, 0])
        
        # Draai de vector 90 graden om een perpendiculaire richting te krijgen
        perpendicular = np.array([-unit_vector[1], unit_vector[0]])
        
        # Verschuif de punten langs de perpendiculaire richting om een breder pad te creëren
        p1_left = tuple((p1 + perpendicular * width / 2).astype(int))
        p1_right = tuple((p1 - perpendicular * width / 2).astype(int))
        p2_left = tuple((p2 + perpendicular * width / 2).astype(int))
        p2_right = tuple((p2 - perpendicular * width / 2).astype(int))
        
        expanded_points.append([p1_left, p2_left, p2_right, p1_right])
    return expanded_points

# Definieer het ArUco-dictionary en de parameters voor detectie
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()

# Pad voor de baan (ovale vorm)
path_points = [
    (300, 100), (350, 50), (450, 50), (550, 125), (650, 100), (700, 100), (750, 200),  
    (750, 300), (700, 400), (650, 400), (550, 350), (450, 350), (350, 300),
    (275, 150), (300, 100)    
]

# Maak het pad breder
expanded_path = expand_path(path_points, width=5)

# Definieer de finishlijn
finish_zone = ((375, 0), (425, 100))

# Variabelen voor ronde detectie
cooldown_time = 2  # Cooldown tijd om meerdere ronde tellingen te voorkomen
last_lap_time = 0  # Tijd van de laatste ronde detectie
lap_text_duration = 2  # Duur om de "Lap Complete" tekst weer te geven

# Variabelen voor het bijhouden van ronden per auto
lap_counts = {0: 1, 1: 1}  # Sla de lap tellingen per marker-id op
last_lap_times = {0: 0, 1: 0}  # Sla de laatste tijd per marker-id op
lap_text_start_times = {0: 0, 1: 0}  # Sla de tekststarttijd per auto op

# Functie om afbeeldingen over te leggen
def overlay_image(background, overlay, x, y, scale_factor=1.0):
    if overlay is None:
        return
    h, w = overlay.shape[:2]
    new_w, new_h = max(1, int(w * scale_factor)), max(1, int(h * scale_factor))
    overlay_resized = cv2.resize(overlay, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    x = max(0, min(x - new_w // 2, background.shape[1] - new_w))
    y = max(0, min(y - new_h // 2, background.shape[0] - new_h))
    
    if overlay_resized.shape[2] == 4:
        alpha = overlay_resized[:, :, 3] / 255.0
        for c in range(3):
            background[y:y+new_h, x:x+new_w, c] = (1 - alpha) * background[y:y+new_h, x:x+new_w, c] + alpha * overlay_resized[:, :, c]
    else:
        background[y:y+new_h, x:x+new_w] = overlay_resized

# Camera instellingen
focal_length = 800  
marker_real_width = 0.1  
initial_scale_factor = 0.2  
min_scale_factor = 0.1  

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Frame error, probeer opnieuw...")
        continue

    # Vergroot de breedte van het frame door zwarte randen toe te voegen
    new_width = frame.shape[1] + 400  # 400 pixels breder maken
    new_height = frame.shape[0]
    
    # Maak een nieuw frame met een zwarte achtergrond
    new_frame = np.zeros((new_height, new_width, 3), dtype=np.uint8)
    
    # Plaats het originele frame in het midden van het nieuwe frame
    new_frame[:, 200:200+frame.shape[1]] = frame

    gray = cv2.cvtColor(new_frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    
    # Pad tekenen
    for points in expanded_path:
        cv2.fillPoly(new_frame, [np.array(points)], (0, 0, 255))  # Rood pad
    
    if ids is not None:
        cv2.aruco.drawDetectedMarkers(new_frame, corners, ids)
        for i, marker_id in enumerate(ids.flatten()):
            x_center = int(np.mean(corners[i][0][:, 0]))
            y_center = int(np.mean(corners[i][0][:, 1]))
            
            width = np.linalg.norm(corners[i][0][0] - corners[i][0][1])
            height = np.linalg.norm(corners[i][0][0] - corners[i][0][3])
            marker_size = (width + height) / 2
            distance = (marker_real_width * focal_length) / marker_size
            
            scale_factor = max(initial_scale_factor * (1 / distance), min_scale_factor)
            
            if marker_id == 1:
                overlay_image(new_frame, green_car, x_center, y_center, scale_factor)
            elif marker_id == 0:
                overlay_image(new_frame, blue_car, x_center, y_center, scale_factor)
            
            # Controleer of de marker zich binnen de finishzone bevindt
            if (finish_zone[0][0] <= x_center <= finish_zone[1][0]) and (finish_zone[0][1] <= y_center <= finish_zone[1][1]):
                current_time = time.time()
                if current_time - last_lap_times[marker_id] > cooldown_time:
                    lap_counts[marker_id] += 1
                    last_lap_times[marker_id] = current_time
                    lap_text_start_times[marker_id] = current_time

    # Display "Lap Complete" en "Finished!" per auto
    for marker_id in lap_counts:
        # Tekst voor de groene auto
        if marker_id == 1:
            if time.time() - lap_text_start_times[marker_id] < lap_text_duration:
                cv2.putText(new_frame, "Lap Complete", (35, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
            
            # Als de groene auto de finish bereikt
            if lap_counts[marker_id] >= 4:
                cv2.putText(new_frame, "Green car finished", (35, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
            
            # Lap Counter voor de groene auto
            if lap_counts[marker_id] >= 4:
                cv2.putText(new_frame, "Finished", (35, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            else:
                cv2.putText(new_frame, f"Lap: {lap_counts[marker_id]}", (35, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        
        # Tekst voor de blauwe auto
        elif marker_id == 0:
            if time.time() - lap_text_start_times[marker_id] < lap_text_duration:
                cv2.putText(new_frame, "Lap Complete", (new_frame.shape[1] - 165, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2, cv2.LINE_AA)
            
            # Als de blauwe auto de finish bereikt
            if lap_counts[marker_id] >= 4:
                cv2.putText(new_frame, "Blue car finished", (new_frame.shape[1] - 165, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2, cv2.LINE_AA)
            
            # Lap Counter voor de blauwe auto
            if lap_counts[marker_id] >= 4:
                cv2.putText(new_frame, "Finished", (new_frame.shape[1] - 165, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            else:
                cv2.putText(new_frame, f"Lap: {lap_counts[marker_id]}", (new_frame.shape[1] - 165, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

    # Toon het frame
    cv2.imshow("ArUco Car Tracking with Lap Detection", new_frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Verlaat het programma
        break
    elif key == ord('r'):  # Reset de lap tellingen
        lap_counts = {0: 1, 1: 1}
        last_lap_times = {0: 0, 1: 0}
        lap_text_start_times = {0: 0, 1: 0}
    elif key == 27:  # ESC afsluiten
        break

cap.release()
cv2.destroyAllWindows()
