#config.py

import cv2

# ---------------------------------------------------------------------------
# Algemeen - Fonts en Text Styling
# ---------------------------------------------------------------------------
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_SIDEBAR = 0.7
FONT_SCALE_RANKING_BAR = 0.5
THICKNESS = 2
LINE_TYPE = cv2.LINE_AA

# ---------------------------------------------------------------------------
# Kleurinstellingen (BGR)
# ---------------------------------------------------------------------------
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (255, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (0, 0, 255)

# ---------------------------------------------------------------------------
# Race Gerelateerde Instellingen
# ---------------------------------------------------------------------------
LAP_COMPLETE_DURATION = 2.0    # Duur (in seconden) dat "Lap Complete" getoond wordt
COOLDOWN_TIME = 1.0            # Minimale tijd tussen het registreren van opeenvolgende lappen
TOTAL_LAPS = 3                 # Totaal aantal te rijden rondes

# ---------------------------------------------------------------------------
# ArUco Marker en Camera Configuratie
# ---------------------------------------------------------------------------
MARKER_REAL_WIDTH = 0.08       # Werkelijke breedte van het marker (in meters, voorbeeld)
FOCAL_LENGTH = 800             # Focale lengte (in pixels, voorbeeld)
INITIAL_SCALE_FACTOR = 0.2
MIN_SCALE_FACTOR = 0.2

# ---------------------------------------------------------------------------
# Ranking Bar Configuratie
# ---------------------------------------------------------------------------
RANKING_BAR_CONFIG = {
    "ranking_bar_height": 100,
    "ranking_bar_background_color": (50, 50, 50),
    "icon_size": 80,
    "text_font": FONT,
    "text_scale": 0.6,
    "text_color": (255, 255, 255),
    "text_thickness": 2,
    "text_offset": 10
}

# ---------------------------------------------------------------------------
# Track en Traject Instellingen
# ---------------------------------------------------------------------------
PATH_POINTS = [(350, 50), (400, 50), (450, 50), (550, 115), (650, 100),
               (700, 100), (750, 200), (750, 300), (700, 400), (650, 400),
               (550, 350), (450, 350), (350, 300), (275, 150), (300, 100), (349, 49)]
PATH_WIDTH = 10 # Breedte van het pad in pixels

# Finish Zone als een rotated rectangle:
# ((center_x, center_y), (width, height), angle in graden)
FINISH_ZONE = ((344, 59), (100, 15), 45)    

# ---------------------------------------------------------------------------
# Camera Instellingen
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0  # Standaard webcam
BLACK_BAR_WIDTH = 200  # Breedte van zijbalken in pixels

# ---------------------------------------------------------------------------
# Posities voor auto-informatie in de zijbalk
# ---------------------------------------------------------------------------
CAR_TEXT_POSITIONS = {
    "blue_car": {
        "lap_position_offset": (20, 50),
        "lap_complete_position_offset": (20, 225)
    },
    "green_car": {
        "lap_position_offset": (175, 50),
        "lap_complete_position_offset": (175, 225)
    }
}

# ---------------------------------------------------------------------------
# Startscherm en Countdown Instellingen
# ---------------------------------------------------------------------------
START_TEXT = "Druk op Enter om te starten"
START_TEXT_POSITION = (300, 300)
START_TEXT_FONT_SCALE = 1
START_TEXT_COLOR = (255, 255, 255)
START_TEXT_THICKNESS = THICKNESS

# Tekst instellingen voor de countdown
COUNTDOWN_FONT_SCALE = 5
COUNTDOWN_COLOR = COLOR_GREEN
COUNTDOWN_THICKNESS = 15
COUNTDOWN_OFFSET_X = 30 # Horizontale offset ten opzichte van het midden van het frame
COUNTDOWN_OFFSET_Y = 0   # Verticale offset ten opzichte van het midden van het frame

# Tekst instellingen voor "GO!"
GO_TEXT = "GO!"
GO_TEXT_FONT_SCALE = 5
GO_TEXT_COLOR = COLOR_GREEN
GO_TEXT_THICKNESS = 15
GO_TEXT_OFFSET_X = 120  # Horizontale offset ten opzichte van het midden van het frame
GO_TEXT_OFFSET_Y = 0   # Verticale Offset ten opzichte van het midden van het frame