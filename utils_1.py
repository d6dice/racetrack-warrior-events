# utils.py

import cv2
import numpy as np
from config_1 import FONT, FONT_SCALE_RANKING_BAR, FONT_SCALE_SIDEBAR, THICKNESS, LINE_TYPE

def overlay_image(background, overlay, x, y, scale_factor=1.0):
    if overlay is None:
        return
    h, w = overlay.shape[:2]
    # Pas de afbeelding aan volgens de schaalfactor
    new_w, new_h = max(1, int(w * scale_factor)), max(1, int(h * scale_factor))
    overlay_resized = cv2.resize(
        overlay,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )
    # Centreer de overlay over de (x, y) positie
    x -= new_w // 2
    y -= new_h // 2
    # Zorg ervoor dat de overlay binnen de grenzen van het frame blijft
    x = max(0, min(int(x), background.shape[1] - new_w))
    y = max(0, min(int(y), background.shape[0] - new_h))
    if overlay_resized.shape[2] == 4:
        alpha = overlay_resized[:, :, 3] / 255.0
        for c in range(3):
            background[y:y+new_h, x:x+new_w, c] = (
                (1 - alpha) * background[y:y+new_h, x:x+new_w, c] +
                alpha * overlay_resized[:, :, c]
            )
    else:
        background[y:y+new_h, x:x+new_w] = overlay_resized

def draw_text(image, text, position, color):
    cv2.putText(
        image, text, position,
        FONT, FONT_SCALE, color, THICKNESS, LINE_TYPE
    )
