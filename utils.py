#utils.py
import cv2
import numpy as np

def overlay_image(background, overlay, center_x, center_y, scale_factor):
    """
    Overlayt de 'overlay'-afbeelding op de 'background' op een specifieke locatie en met een bepaalde schaal.
    
    De functie schaalt eerst de overlay-afbeelding met de gegeven scale_factor. Vervolgens wordt
    de overlay zo geplaatst dat het middelpunt (center_x, center_y) overeenkomt met het middelpunt van de overlay.
    Als de overlay een alpha-kanaal (transparantie) bevat, wordt alpha blending toegepast; anders wordt de overlay direct gekopieerd.
    
    Args:
        background (numpy.ndarray): De achtergrondafbeelding (BGR) waarop overlegd wordt.
        overlay (numpy.ndarray): De overlay-afbeelding, die optioneel een alpha-kanaal kan hebben.
        center_x (int): De x-coördinaat van het middelpunt waar de overlay geplaatst moet worden.
        center_y (int): De y-coördinaat van het middelpunt waar de overlay geplaatst moet worden.
        scale_factor (float): De factor waarmee de overlay geschaald wordt.
    
    Returns:
        numpy.ndarray: De achtergrondafbeelding met de overlay erop gelegd.
    """
    # Schaal de overlay-afbeelding
    overlay_resized = cv2.resize(overlay, None, fx=scale_factor, fy=scale_factor)
    h, w = overlay_resized.shape[:2]
    
    # Bepaal de top-left hoek zodat de overlay wordt gecentreerd op (center_x, center_y)
    x1 = int(center_x - w / 2)
    y1 = int(center_y - h / 2)
    x2 = x1 + w
    y2 = y1 + h

    # Bepaal de regio van interesse (ROI) op de achtergrond en de overlay indien de overlay buiten de grenzen valt.
    bg_h, bg_w = background.shape[:2]
    
    overlay_x1, overlay_y1 = 0, 0
    overlay_x2, overlay_y2 = w, h

    # Indien de overlay buiten de grenzen valt, pas de ROI aan
    if x1 < 0:
        overlay_x1 = -x1
        x1 = 0
    if y1 < 0:
        overlay_y1 = -y1
        y1 = 0
    if x2 > bg_w:
        overlay_x2 = w - (x2 - bg_w)
        x2 = bg_w
    if y2 > bg_h:
        overlay_y2 = h - (y2 - bg_h)
        y2 = bg_h

    # Indien de ROI geen geldige dimensies heeft, doen we niets.
    if overlay_x1 >= overlay_x2 or overlay_y1 >= overlay_y2:
        return background

    # Verkrijg de ROI van de achtergrond
    roi = background[y1:y2, x1:x2]
    overlay_part = overlay_resized[overlay_y1:overlay_y2, overlay_x1:overlay_x2]

    # Als overlay een alfa-kanaal heeft, gebruik alpha blending.
    if overlay_part.shape[2] == 4:
        overlay_bgr = overlay_part[:, :, :3]
        alpha_mask = overlay_part[:, :, 3] / 255.0  # Normaliseer naar [0, 1]
        alpha_mask = np.dstack([alpha_mask] * 3)      # Zet om naar 3 kanalen voor BGR
        roi[:] = (overlay_bgr * alpha_mask + roi * (1 - alpha_mask)).astype(roi.dtype)
    else:
        # Anders, kopieer de overlay direct over de ROI.
        roi[:] = overlay_part

    return background
