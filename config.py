#config.py
import cv2
import numpy as np

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
COLOR_RANKING_BAR_BG = (50, 50, 50)
COLOR_TRACK = (0, 0, 255)  # Voor het tekenen van de track (bijvoorbeeld een polyline)

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
# Auto Configuratie
# Voeg hier eenvoudig nieuwe auto's toe of verwijder ze.
# Alle relevante eigenschappen (zoals afbeelding, username, marker_id, positieoffsets, enz.) komen hier samen.
# ---------------------------------------------------------------------------
CAR_CONFIG = {
    "blue_car": {
        "username": "Marieke",
        "marker_id": 0,  # Zorg dat deze overeenkomt met de ArUco-marker
        "image_path": r"D:\werk\warrior events\blauwe_auto.png",
        "width": 640,
        "height": 480,
        "lap_position_offset": (675, 75),
        "lap_complete_position_offset": (675, 225),
        "sidebar_text_color": (255, 0, 0)
    },
    "green_car": {
        "username": "Panda",
        "marker_id": 1,
        "image_path": r"D:\werk\warrior events\groene_auto.png",
        "width": 640,
        "height": 480,
        "lap_position_offset": (-175, 75),
        "lap_complete_position_offset": (-175, 225),
        "sidebar_text_color": (0, 255, 0)
    },
    "orange_car": {
        "username": "Petan",
        "marker_id": 2,
        "image_path": r"D:\werk\warrior events\oranje_auto.png",
        "width": 640,
        "height": 480,
        "lap_position_offset": (675, 300),  
        "lap_complete_position_offset": (675, 450),
        "sidebar_text_color": (0, 165, 255)
    },
    "red_car": {
        "username": "Demi",
        "marker_id": 3,
        "image_path": r"D:\werk\warrior events\rode_auto.png",
        "width": 640,
        "height": 480,
        "lap_position_offset": (-175, 300),  
        "lap_complete_position_offset": (-175, 450),
        "sidebar_text_color": (0, 0, 255)
        }
}
# ---------------------------------------------------------------------------
# Afbeeldingslocaties en icon-instellingen
# ---------------------------------------------------------------------------

ICON_SIZE = 80  # Breedte en hoogte van auto-afbeeldingen in de rankingbar

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
# Ranking Labels Configuratie
# ---------------------------------------------------------------------------
RANKING_LABELS = {
    1: "Eerste",
    2: "Tweede",
    3: "Derde",
    # Voor overige posities kun je of een vaste tekst gebruiken of een formule toepassen:
    "default": "Laatste"
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
# position indicators
# ---------------------------------------------------------------------------
POSITION_INDICATOR_CONFIG = {
    "radius_factor": 50,           # Basisstraal voor de indicator (wordt vermenigvuldigd met de schaalfactor van de auto)
    "offset": (-30, -150),           # (x, y)-offset voor de indicator ten opzichte van de auto’s positie
    "text_scale": 2.0,             # Basistekstschaling (wordt vermenigvuldigd met de auto schaalfactor)
    "text_color": (0, 0, 0),         # Textkleur (BGR)
    "line_thickness": 2,           # Dikte van de getekende tekst
    "colors": {                    # Definieer de kleur per positie (rang)
         1: (0, 215, 255),         # Goud voor positie 1
         2: (192, 192, 192),         # Zilver voor positie 2
         3: (205, 127, 50),         # Brons voor positie 3
         "default": (255, 255, 255)  # Wit als fallback (voor positie 4 en verder)
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

# ---------------------------------------------------------------------------
# eindklassement instellingen
# ---------------------------------------------------------------------------
FINAL_OVERLAY_CONFIG = {
    "overlay_color": (255, 255, 255),       # wit
    "alpha": 0.6,                   # Transparantie (60%)
    "width_ratio": 0.5,             # Overlay breedte = 50% van de framebreedte
    "height_ratio": 0.7,            # Overlay hoogte = 70% van de framehoogte
    "margin": 10,                   # Marges binnen de overlay, voor tekst
    "title_text": "Final Ranking",
    "title_font_scale": 1.2,
    "title_thickness": 2,
    "text_font": cv2.FONT_HERSHEY_SIMPLEX,
    "text_font_scale": 1.0,
    "text_thickness": 2,
    "text_color": (0, 0, 0)     # zwart
    
}

FINAL_OVERLAY_DELAY = 3.0  # Vertraag de finale overlay met 3 seconden

