import cv2
import numpy as np
import config  # Zorg dat dit verwijst naar jouwe config.py waarin RANKING_LABELS staat

def draw_ranking_bar(frame, sorted_cars, ranking_bar_config):
    """
    Tekent de ranking bar op het gegeven frame.
    
    Deze functie tekent onderaan het frame een balk waarin voor elke auto:
      - Een icoon (auto-afbeelding) wordt weergegeven, geschaald naar een vaste grootte.
      - Een tekstuele ranking (bijvoorbeeld "Eerste", "Tweede", "Derde", of een fallback nummer) 
        wordt getoond.
        
    Configuratie-instellingen (via de 'ranking_bar_config'-dict) omvatten:
      - ranking_bar_height: de hoogte van de ranking bar.
      - ranking_bar_background_color: de achtergrondkleur van de balk (B, G, R).
      - icon_size: de gewenste breedte en hoogte waarin de auto-afbeelding getekend wordt.
      - text_font: het OpenCV-lettertype dat gebruikt wordt voor de ranking-teksten.
      - text_scale: de schaalfactor voor de ranking-teksten.
      - text_color: de kleur voor de ranking-teksten.
      - text_thickness: de lijndikte voor de ranking-teksten.
      - text_offset: een verticale offset (in pixels) van de tekst (bijvoorbeeld vanaf de onderkant van het frame).
      - ranking_labels: een dictionary met ranking nummers als key en de tekstuele representatie als value.
    
    Args:
        frame (numpy.ndarray): Het frame waarop de ranking bar wordt getekend.
        sorted_cars (list): Een gesorteerde lijst van Car-objecten, waarbij de auto met de beste positie eerst komt.
        ranking_bar_config (dict): Een dictionary met configuratieparameters voor de ranking bar.
    
    Returns:
        numpy.ndarray: Het frame met de getekende ranking bar.
    """
    # Haal de configuratieparameters op, met defaultwaarden indien de sleutel niet aanwezig is.
    ranking_bar_height = ranking_bar_config.get("ranking_bar_height", 100)
    ranking_bar_bg_color = ranking_bar_config.get("ranking_bar_background_color", (50, 50, 50))
    icon_size = ranking_bar_config.get("icon_size", 80)
    text_font = ranking_bar_config.get("text_font", cv2.FONT_HERSHEY_SIMPLEX)
    text_scale = ranking_bar_config.get("text_scale", 0.6)
    text_color = ranking_bar_config.get("text_color", (255, 255, 255))
    text_thickness = ranking_bar_config.get("text_thickness", 2)
    text_offset = ranking_bar_config.get("text_offset", 10)
    
    # Haal de rankinglabels op uit de meegegeven config, of anders uit de globale config.
    ranking_labels = ranking_bar_config.get("ranking_labels", None)
    if ranking_labels is None:
        ranking_labels = getattr(config, "RANKING_LABELS", {})

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
        # Bereken de gecentreerde positie voor het auto-icoon.
        icon_center_x = spacing * (idx + 1)
        icon_center_y = bar_y + ranking_bar_height // 2

        # Stap 3a: Indien de auto-afbeelding beschikbaar is, teken deze in het kader.
        if hasattr(car, "car_image") and car.car_image is not None:
            # Verklein of schaal de auto-afbeelding tot icon_size x icon_size
            icon = cv2.resize(car.car_image, (icon_size, icon_size))
            # Bereken de linkerbovenhoek zodat het icoon gecentreerd getekend wordt.
            x1 = icon_center_x - icon_size // 2
            y1 = icon_center_y - icon_size // 2
            x2 = x1 + icon_size
            y2 = y1 + icon_size

            # Controleer of de ROI binnen de grenzen van het frame valt.
            if x1 >= 0 and y1 >= bar_y and x2 <= frame_width and y2 <= frame_height:
                # Indien de afbeelding een alpha-kanaal heeft, gebruik dan enkel BGR-kanalen.
                if icon.shape[2] == 4:
                    icon = icon[:, :, :3]
                frame[y1:y2, x1:x2] = icon

        # Stap 3b: Stel de rankingtekst in d.m.v. de rankinglabels.
        # Hier gaan we ervan uit dat 'car.position' al is bepaald (bijv. 1, 2, 3, etc.)
        rank = car.position  
        ranking_text = ranking_labels.get(rank, ranking_labels.get("default", f"{rank}"))
                
        # Bereken de grootte van de tekst zodat je deze kunt centreren.
        (text_width, text_height), _ = cv2.getTextSize(ranking_text, text_font, text_scale, text_thickness)
        text_x = icon_center_x - text_width // 2
        # Zet de tekst dicht bij de onderkant van het frame (met text_offset)
        text_y = frame_height - text_offset
        cv2.putText(frame, ranking_text, (text_x, text_y), text_font, text_scale, text_color, text_thickness, cv2.LINE_AA)

    return frame