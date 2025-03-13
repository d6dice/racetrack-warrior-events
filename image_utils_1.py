# image_utils_1.py

import cv2
def load_image(path, max_width, max_height):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Afbeelding niet gevonden: {path}")
        return None
    h, w = img.shape[:2]
    scale = min(max_width / w, max_height / h) if (w > max_width or h > max_height) else 1
    return cv2.resize(
        img,
        (int(w * scale), int(h * scale)),
        interpolation=cv2.INTER_AREA
    )
