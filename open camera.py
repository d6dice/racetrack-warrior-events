# Code om camera te openen

import cv2

# Open de camera (0 is meestal de standaardcamera)
camera = cv2.VideoCapture(2)

if not camera.isOpened():
    print("Kan de camera niet openen!")
    exit()

while True:
    # Lees een frame van de camera
    ret, frame = camera.read()
    
    if not ret:
        print("Kon geen frame lezen. Camera gestopt.")
        break

    # Toon het frame in een venster
    cv2.imshow("Camera", frame)

    # Breek de loop als de gebruiker op 'q' drukt
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Camera vrijgeven en vensters sluiten
camera.release()
cv2.destroyAllWindows()
