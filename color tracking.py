color tracking:

import cv2 
import numpy as np

# Open de videofeed van OBS Studio (meestal ID 1 of 2)
cap = cv2.VideoCapture(2)

# Pas de camera-eigenschappen aan om overbelichting te verminderen
cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
cap.set(cv2.CAP_PROP_SATURATION, 0.5)

# Maak een window voor de trackbars
cv2.namedWindow('HSV Trackbars')

# Maak trackbars voor het aanpassen van de HSV-bereiken
cv2.createTrackbar('Lower H', 'HSV Trackbars', 40, 179, lambda x: None)
cv2.createTrackbar('Lower S', 'HSV Trackbars', 70, 255, lambda x: None)
cv2.createTrackbar('Lower V', 'HSV Trackbars', 70, 255, lambda x: None)
cv2.createTrackbar('Upper H', 'HSV Trackbars', 80, 179, lambda x: None)
cv2.createTrackbar('Upper S', 'HSV Trackbars', 255, 255, lambda x: None)
cv2.createTrackbar('Upper V', 'HSV Trackbars', 255, 255, lambda x: None)

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        break

    # Converteer het frame naar HSV kleurmodel
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Haal de huidige posities van de trackbars op
    lower_h = cv2.getTrackbarPos('Lower H', 'HSV Trackbars')
    lower_s = cv2.getTrackbarPos('Lower S', 'HSV Trackbars')
    lower_v = cv2.getTrackbarPos('Lower V', 'HSV Trackbars')
    upper_h = cv2.getTrackbarPos('Upper H', 'HSV Trackbars')
    upper_s = cv2.getTrackbarPos('Upper S', 'HSV Trackbars')
    upper_v = cv2.getTrackbarPos('Upper V', 'HSV Trackbars')

    # Definieer het HSV-bereik voor de kleur
    lower_color = np.array([lower_h, lower_s, lower_v])
    upper_color = np.array([upper_h, upper_s, upper_v])

    # Maak een masker voor de geselecteerde kleur
    mask = cv2.inRange(hsv, lower_color, upper_color)

    # Pas morfologische bewerkingen toe om ruis te verminderen
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Zoek contouren in het masker
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Filter kleine contouren eruit
        if cv2.contourArea(contour) > 500:
            # Verkrijg de bounding box van de contour
            x, y, w, h = cv2.boundingRect(contour)
            # Teken de bounding box op het originele frame
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Toon het originele frame met het getrackte object
    cv2.imshow('Object Tracking', frame)
    # Toon het masker (optioneel)
    cv2.imshow('Mask', mask)

    # Stop de loop bij het indrukken van de 'q'-toets
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release de video capture en sluit alle vensters
cap.release()
cv2.destroyAllWindows()
