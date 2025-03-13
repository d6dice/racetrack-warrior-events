import cv2
import os

# Controleer OpenCV-versie
print(f"OpenCV-versie: {cv2.__version__}")

# Controleer de beschikbare attributen in cv2.aruco
if hasattr(cv2, 'aruco'):
    print("Beschikbare functies in cv2.aruco:")
    print(dir(cv2.aruco))
else:
    print("De ArUco-module is niet beschikbaar in de geïnstalleerde OpenCV-versie.")
    exit()

# Probeer een ArUco-marker te genereren
try:
    # Haal een vooraf gedefinieerd woordenboek op
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    # Marker-ID en grootte instellen
    marker_id = 3
    marker_size = 200

    # Genereer de ArUco-marker
    marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)

    # Bestemmingspad instellen
    file_path = "marker_3.png"

    # Opslaan als afbeelding
    cv2.imwrite(file_path, marker)
    print(f"ArUco-marker succesvol gegenereerd en opgeslagen als '{file_path}'.")

    # Print de locatie van het bestand
    absolute_path = os.path.abspath(file_path)
    print(f"Het bestand is opgeslagen op: {absolute_path}")

    # Laat de ArUco-code zien
    print(f"ArUco marker ID: {marker_id}")
    
    # Optioneel: marker weergeven in een nieuw venster
    cv2.imshow("ArUco Marker", marker)
    cv2.waitKey(0)  # Wacht tot een toets wordt ingedrukt
    cv2.destroyAllWindows()

except AttributeError as e:
    print("Er trad een fout op bij het genereren van de marker:")
    print(e)
    print("Controleer of de ArUco-module correct is geïnstalleerd en up-to-date.")
except Exception as e:
    print(f"Er trad een onverwachte fout op: {e}")
