#code om aruco code te tracken
import cv2
import os

# Controleer OpenCV-versie
print(f"OpenCV-versie: {cv2.__version__}")

# Controleer of cv2.aruco beschikbaar is
if hasattr(cv2, 'aruco'):
    print("Beschikbare functies in cv2.aruco:")
    print(dir(cv2.aruco))
else:
    print("De ArUco-module is niet beschikbaar in de geïnstalleerde OpenCV-versie.")
    exit()

# Kies een ArUco-dictionary (4x4, 50 markers)
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()  # Aangepast hier

# Open de camera
cap = cv2.VideoCapture(0)

while True:
    # Lees een frame van de camera
    ret, frame = cap.read()

    # Zet het frame om naar grijswaarden
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detecteer ArUco-markers in het frame
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    # Als markers zijn gedetecteerd
    if ids is not None:
        # Teken de markers op het beeld
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        # Voeg tekst toe aan het beeld
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, 'Code herkend', (50, 50), font, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Toon het resultaat
    cv2.imshow("ArUco Code Detectie", frame)

    # Als de 'q' toets wordt ingedrukt, stop dan de loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Sluit de camera en alle vensters
cap.release()
cv2.destroyAllWin0dows()
