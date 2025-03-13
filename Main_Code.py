#2 aruco codes waar verschillende auto’s op afgebeeld worden die vast zitten aan de aruco
import cv2  
import numpy as np

# Controleer OpenCV-versie
print(f"OpenCV-versie: {cv2.__version__}")

# Controleer of cv2.aruco beschikbaar is
if not hasattr(cv2, 'aruco'):
    print("De ArUco-module is niet beschikbaar in de geïnstalleerde OpenCV-versie.")
    exit()

# Kies een ArUco-dictionary
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()

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

# Webcam frame-afmetingen
green_car = load_image('D:\\werk\\warrior events\\groene_auto.png', 640, 480)
blue_car = load_image('D:\\werk\\warrior events\\blauwe_auto.png', 640, 480)

# Overlay functie
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

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    
    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        for i, marker_id in enumerate(ids.flatten()):
            x_center = int(np.mean(corners[i][0][:, 0]))
            y_center = int(np.mean(corners[i][0][:, 1]))
            
            width = np.linalg.norm(corners[i][0][0] - corners[i][0][1])
            height = np.linalg.norm(corners[i][0][0] - corners[i][0][3])
            marker_size = (width + height) / 2  
            distance = (marker_real_width * focal_length) / marker_size
            
            scale_factor = max(initial_scale_factor * (1 / distance), min_scale_factor)
            
            if marker_id == 1:
                overlay_image(frame, green_car, x_center, y_center, scale_factor)
            elif marker_id == 0:
                overlay_image(frame, blue_car, x_center, y_center, scale_factor)
    
    cv2.imshow("ArUco Code Detectie", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
