# config.py

import cv2

# Lettertype-instellingen
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_SIDEBAR = 0.7  # Tekstgrootte voor de zijbalken
FONT_SCALE_RANKING_BAR = 0.5  # Tekstgrootte voor de onderste balk
THICKNESS = 2
LINE_TYPE = cv2.LINE_AA

# Kleuren (BGR-formaat)
COLOR_GREEN = (0, 255, 0)   # Groene kleur voor de groene auto
COLOR_BLUE = (255, 0, 0)    # Blauwe kleur voor de blauwe auto
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (0, 0, 255)

# Tijd instellingen
LAP_COMPLETE_DURATION = 2    # Duur om "Lap Complete" weer te geven (in seconden)
COOLDOWN_TIME = 2            # Cooldown tijd om meerdere ronde tellingen te voorkomen (in seconden)

# Marker instellingen
MARKER_REAL_WIDTH = 0.1      # Werkelijke breedte van de marker in meters
FOCAL_LENGTH = 800           # Brandpuntsafstand voor afstandsberekening
INITIAL_SCALE_FACTOR = 0.2   # Initiële schaalfactor voor auto-afbeeldingen
MIN_SCALE_FACTOR = 0.1       # Minimale schaalfactor voor auto-afbeeldingen

# Ranking bar configuratie
RANKING_BAR_CONFIG = {
    'ranking_bar_height': 200,
    'positions': ['Eerste plaats', 'Tweede plaats'],
    'y_offset': 120,
    'text_spacing': 50,
    'car_scale_multiplier': 4,
    'text_font': FONT,
    'text_font_scale': FONT_SCALE_RANKING_BAR,
    'text_color': COLOR_WHITE,
    'text_thickness': THICKNESS,
    'text_line_type': LINE_TYPE,
    'car_image_offset_x': 35,
    'car_image_offset_y': 20,
    'car_image_offset_ranking_bar_x': 10,
    'text_offset_x': 0,
}

# Pad instellingen voor de baan (ovale vorm)
PATH_POINTS = [
    (300, 100), (350, 50), (450, 50), (550, 125), (650, 100),
    (700, 100), (750, 200), (750, 300), (700, 400), (650, 400),
    (550, 350), (450, 350), (350, 300), (275, 150), (300, 100)
]
PATH_WIDTH = 5                # Breedte van het pad

# Finish lijn instellingen
FINISH_ZONE = ((375, 0), (425, 100))  # Coördinaten van de finishzone

# Camera instellingen
CAMERA_INDEX = 0             # Index van de camera voor cv2.VideoCapture

# Zwarte balk instellingen (voor frame uitbreiding)
BLACK_BAR_WIDTH = 200        # Breedte van de zwarte balken aan de zijkanten

# Tekst instellingen voor het startscherm
START_TEXT = "Druk op Enter om te beginnen"
START_TEXT_POSITION = (300, 300)
START_TEXT_FONT_SCALE = 1.0
START_TEXT_COLOR = COLOR_WHITE
START_TEXT_THICKNESS = THICKNESS

# Tekst instellingen voor de countdown
COUNTDOWN_FONT_SCALE = 5
COUNTDOWN_COLOR = COLOR_GREEN
COUNTDOWN_THICKNESS = 15
# Offset ten opzichte van het midden van het frame
COUNTDOWN_OFFSET_X = 30 # Horizontale offset
COUNTDOWN_OFFSET_Y = 0   # Verticale offset

# Tekst instellingen voor "GO!"
GO_TEXT = "GO!"
GO_TEXT_FONT_SCALE = 5
GO_TEXT_COLOR = COLOR_GREEN
GO_TEXT_THICKNESS = 15
# Offset ten opzichte van het midden van het frame
GO_TEXT_OFFSET_X = 120  # Horizontale offset
GO_TEXT_OFFSET_Y = 0   # Verticale offset
