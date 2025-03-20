import cv2
import numpy as np

def draw_ranking_bar(frame, sorted_cars, config):
    """
    Tekent de ranking bar op het gegeven frame.
    
    Deze functie tekent onderaan het frame een balk waarin voor elke auto:
      - Een icoon (auto-afbeelding) wordt weergegeven, geschaald naar een vaste grootte.
      - Een tekstuele ranking (bijvoorbeeld "Eerste", "Tweede", "Derde", of een fallback nummer) 
        wordt getoond.
        
    Hierbij worden de volgende configuratie-instellingen gebruikt (via de 'config'-dict):
      - ranking_bar_height: de hoogte van de ranking bar.
      - ranking_bar_background_color: de achtergrondkleur van de balk (B, G, R).
      - icon_size: de gewenste breedte en hoogte (vaak gelijk) waarin de auto-afbeelding getekend wordt.
      - text_font: het OpenCV-lettertype dat gebruikt wordt voor de ranking-teksten.
      - text_scale: de schaalfactor voor de ranking-teksten.
      - text_color: de kleur voor de ranking-teksten.
      - text_thickness: de lijndikte voor de ranking-teksten.
      - text_offset: een verticale offset (in pixels) van de tekst (bijvoorbeeld vanaf de onderkant van het frame).
    
    Args:
        frame (numpy.ndarray): Het frame waarop de ranking bar wordt getekend.
        sorted_cars (list): Een gesorteerde lijst van Car-objecten, waarbij de eerste auto op de hoogste positie staat.
        config (dict): Een dictionary met configuratieparameters voor de ranking bar (zie hierboven).
    
    Returns:
        numpy.ndarray: Het frame met de getekende ranking bar.
    """
    # Haal de configuratieparameters op, met standaardwaarden indien de sleutel niet aanwezig is.
    ranking_bar_height = config.get("ranking_bar_height", 100)
    ranking_bar_bg_color = config.get("ranking_bar_background_color", (50, 50, 50))
    icon_size = config.get("icon_size", 80)
    text_font = config.get("text_font", cv2.FONT_HERSHEY_SIMPLEX)
    text_scale = config.get("text_scale", 0.6)
    text_color = config.get("text_color", (255, 255, 255))
    text_thickness = config.get("text_thickness", 2)
    text_offset = config.get("text_offset", 10)

    # Bepaal de afmetingen van het frame
    frame_height, frame_width = frame.shape[:2]
    
    # De ranking bar wordt meestal in de onderste balk getekend; bepaal de y-positie hiervan:
    bar_y = frame_height - ranking_bar_height

    # Stap 1: Teken de achtergrond van de ranking bar als een rechthoek
    cv2.rectangle(frame, (0, bar_y), (frame_width, frame_height), ranking_bar_bg_color, -1)

    # Bepaal het aantal auto's dat getoond moet worden
    num_cars = len(sorted_cars)
    if num_cars == 0:
        return frame

    # Stap 2: Bepaal de horizontale spacing zodat elk icoon evenredig wordt verdeeld.
    spacing = frame_width // (num_cars + 1)

    # Stap 3: Voor elke auto in de gesorteerde lijst:
    for idx, car in enumerate(sorted_cars):
        # Bereken de gecentreerde positie (icon_center_x) voor het auto-icoon:
        icon_center_x = spacing * (idx + 1)
        # Het centrum van het icoon in de balk (verticaal gecentreerd in de ranking bar)
        icon_center_y = bar_y + ranking_bar_height // 2

        # Stap 3a: Indien de auto-afbeelding beschikbaar is, teken deze in het kader.
        if hasattr(car, "car_image") and car.car_image is not None:
            # Verklein of verhoog de auto-afbeelding tot icon_size x icon_size
            icon = cv2.resize(car.car_image, (icon_size, icon_size))
            # Bepaal de linkerbovenhoek zodat het icoon gecentreerd wordt getekend
            x1 = icon_center_x - icon_size // 2
            y1 = icon_center_y - icon_size // 2
            x2 = x1 + icon_size
            y2 = y1 + icon_size

            # Controleer of de ROI (Region of Interest) binnen de grenzen van het frame valt
            if x1 >= 0 and y1 >= bar_y and x2 <= frame_width and y2 <= frame_height:
                # Indien de afbeelding een alpha-kanaal heeft, verwijdert deze de alfa (geeft enkel de BGR-kanalen)
                if icon.shape[2] == 4:
                    icon = icon[:, :, :3]
                frame[y1:y2, x1:x2] = icon

        # Stap 3b: Stel een tekst in die de positie aangeeft (bijvoorbeeld "Eerste", "Tweede",...)
        if car.position == 1:
            ranking_text = "Eerste"
        elif car.position == 2:
            ranking_text = "Tweede"
        elif car.position == 3:
            ranking_text = "Derde"
        else:
            ranking_text = f"{car.position}"  # Gebruik het nummer als fallback

        # Bereken de grootte van de tekst zodat je deze kunt centreren: 
        (text_width, text_height), _ = cv2.getTextSize(ranking_text, text_font, text_scale, text_thickness)
        text_x = icon_center_x - text_width // 2
        # Zet de tekst dicht bij de onderkant van het frame (of pas dit aan met text_offset)
        text_y = frame_height - text_offset
        cv2.putText(frame, ranking_text, (text_x, text_y), text_font, text_scale, text_color, text_thickness, cv2.LINE_AA)

    return frame
