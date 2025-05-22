# image_utils.py
import cv2
import numpy as np
from config import BLACK_BAR_WIDTH, RANKING_BAR_CONFIG

def load_image(path, width=None, height=None):
    """
    Laadt een afbeelding via OpenCV en schaalt deze (optioneel) naar de opgegeven
    breedte en hoogte.

    Args:
        path (str): Het bestandspad naar de afbeelding.
        width (int, optional): De gewenste breedte. Als None blijft de originele breedte.
        height (int, optional): De gewenste hoogte. Als None blijft de originele hoogte.

    Returns:
        numpy.ndarray: De geladen (en geschaalde) afbeelding.

    Raises:
        FileNotFoundError: Als de afbeelding niet gevonden is.
    """
    # Probeer de afbeelding te laden
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Afbeelding '{path}' niet gevonden.")
    
    # Als breedte en hoogte zijn meegegeven, schaal de afbeelding
    if width is not None and height is not None:
        img = cv2.resize(img, (width, height))
        
    return img

def overlay_transparent(background, overlay, x, y, overlay_size=None):
    """
    Past een transparante overlay (met een alpha kanaal) toe op het 'background'-beeld op de
    positie (x, y). Dit wordt gebruikt als de overlay-afbeelding transparantie bevat 
    (bijvoorbeeld voor logo's of iconen).

    Parameters:
        background (numpy.ndarray): Het basisbeeld (BGR).
        overlay (numpy.ndarray): De overlay-afbeelding met 4 kanalen (B, G, R, A).
        x (int): De x-coördinaat waar de overlay moet worden geplaatst.
        y (int): De y-coördinaat waar de overlay moet worden geplaatst.
        overlay_size (tuple, optional): Als opgegeven, schaalt de overlay naar (width, height).

    Returns:
        numpy.ndarray: Het achtergrondbeeld met de transparante overlay toegepast.
    """
    bg = background.copy()
    if overlay_size is not None:
        overlay = cv2.resize(overlay, overlay_size, interpolation=cv2.INTER_AREA)
    
    h, w = overlay.shape[:2]

    # Als de overlay buiten het achtergrondbeeld valt, doe niets
    if x >= bg.shape[1] or y >= bg.shape[0]:
        return bg

    # Definieer het gebied (ROI) op het achtergrondbeeld waar de overlay moet komen
    roi = bg[y:y+h, x:x+w]

    # Split de overlay af in de BGR-component en het alpha-kanaal (transparantie)
    overlay_img = overlay[..., :3]
    mask = overlay[..., 3:] / 255.0  # Masker normaliseren naar bereik 0-1

    # Combineer de overlay en de ROI via blending
    roi = (1 - mask) * roi + mask * overlay_img
    bg[y:y+h, x:x+w] = roi.astype(np.uint8)
    return bg

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
    # Veiligheid: als de coördinaten None zijn, sla dan de overlay over.
    if center_x is None or center_y is None:
        print("Warning: overlay_image aangeroepen met None-coördinaten; overlay overslaan.")
        return background
    
    # Schaal de overlay-afbeelding
    overlay_resized = cv2.resize(overlay, None, fx=scale_factor, fy=scale_factor)
    h, w = overlay_resized.shape[:2]
    
    # Bereken de bovenste linkerhoek zodat de overlay gecentreerd wordt op (center_x, center_y)
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

def display_camera_feed(cap, stop_event, base_overlay, shared_frame, frame_lock):
    """
    Toon de live camera feed en werk de frames bij via een gedeelde buffer.
    """
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("❌ Geen frame beschikbaar van de camera.")
            break

        # Zorg ervoor dat de afmetingen van frame overeenkomen met de camera-regio
        expected_width = base_overlay.shape[1] - 2 * BLACK_BAR_WIDTH
        expected_height = base_overlay.shape[0] - RANKING_BAR_CONFIG['ranking_bar_height']
        
        if frame.shape[1] != expected_width or frame.shape[0] != expected_height:
            frame = cv2.resize(frame, (expected_width, expected_height))

        with frame_lock:
            if shared_frame[0] is not None:
                frame = shared_frame[0]

        # Voeg de basisoverlay toe
        composite_frame = base_overlay.copy()
        cam_region = (slice(0, frame.shape[0]), slice(BLACK_BAR_WIDTH, BLACK_BAR_WIDTH + frame.shape[1]))
        composite_frame[cam_region] = frame

        # Toon het gecombineerde frame
        cv2.imshow("Race Track", composite_frame)

        # Controleer op afsluiten
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break

    cap.release()
    cv2.destroyAllWindows()