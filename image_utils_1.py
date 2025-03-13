# image_utils_1.py

import cv2

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
