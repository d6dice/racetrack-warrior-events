# ranking_bar.py

import cv2

def draw_ranking_bar(frame, sorted_cars, config):
    """
    Tekent de ranking bar op het gegeven frame.
    
    De ranking bar wordt typisch als een balk onderaan het frame getekend en toont voor elke auto:
     - De auto-afbeelding (geschaald naar een vast formaat)
     - Het positie getal (ranking)

    Args:
        frame (numpy.ndarray): Het frame waarop de ranking bar wordt getekend.
        sorted_cars (list): Een gesorteerde lijst van Car-objecten, waarbij de eerste auto op de eerste plaats staat.
        config (dict): Configuratieparameters voor de ranking bar. Mogelijke keys:
            - ranking_bar_height (int): De hoogte van de ranking bar.
            - ranking_bar_background_color (tuple): Achtergrondkleur van de ranking bar (B, G, R).
            - icon_size (int): De gewenste breedte en hoogte voor elke auto-afbeelding in de balk.
            - text_font: cv2-lettertype voor de positie-teksten.
            - text_scale (float): Schaalfactor voor de positie-teksten.
            - text_color (tuple): Kleur (B,G,R) voor de positie-teksten.
            - text_thickness (int): Dikte van de positie-teksten.
            - text_offset (int): Verticale offset van de tekst ten opzichte van de balkonderkant.
    
    Returns:
        numpy.ndarray: Het frame met de getekende ranking bar.
    """
    ranking_bar_height = config.get("ranking_bar_height", 100)
    ranking_bar_bg_color = config.get("ranking_bar_background_color", (50, 50, 50))
    icon_size = config.get("icon_size", 80)
    text_font = config.get("text_font", cv2.FONT_HERSHEY_SIMPLEX)
    text_scale = config.get("text_scale", 0.6)
    text_color = config.get("text_color", (255, 255, 255))
    text_thickness = config.get("text_thickness", 2)
    text_offset = config.get("text_offset", 10)

    frame_height, frame_width = frame.shape[:2]
    bar_y = frame_height - ranking_bar_height

    # Teken de achtergrond (ranking bar) als een rechthoek over de onderste balk
    cv2.rectangle(frame, (0, bar_y), (frame_width, frame_height), ranking_bar_bg_color, -1)

    num_cars = len(sorted_cars)
    if num_cars == 0:
        return frame

    # Bepaal de horizontale spacing zodat de iconen netjes verdeeld worden
    spacing = frame_width // (num_cars + 1)

    for idx, car in enumerate(sorted_cars):
        # De horizontale positie voor dit icoon (gecentreerd in het vakje)
        icon_center_x = spacing * (idx + 1)
        icon_center_y = bar_y + ranking_bar_height // 2

        # Zorgt ervoor dat de auto-afbeelding aanwezig is
        if hasattr(car, "car_image") and car.car_image is not None:
            # Zorg dat de auto-afbeelding wordt geschaald naar icon_size x icon_size
            icon = cv2.resize(car.car_image, (icon_size, icon_size))

            # Bereken de plaatsing zodat het icoon gecentreerd is
            x1 = icon_center_x - icon_size // 2
            y1 = icon_center_y - icon_size // 2
            x2 = x1 + icon_size
            y2 = y1 + icon_size

            # Controleer of de ROI binnen framegrenzen valt
            if x1 >= 0 and y1 >= bar_y and x2 <= frame_width and y2 <= frame_height:
                # Als de auto-afbeelding een alpha-kanaal (4 kanalen) heeft, verwijder dat kanaal.
                if icon.shape[2] == 4:
                    icon = icon[:, :, :3]
                frame[y1:y2, x1:x2] = icon
                
        # Zet hier de gewenste tekst in plaats van het getal.
        if car.position == 1:
            ranking_text = "Eerste"
        elif car.position == 2:
            ranking_text = "Tweede"
        elif car.position == 3:
            ranking_text = "Derde"
        else:
            ranking_text = f"{car.position}"  # Of een andere fallback

        (text_width, text_height), _ = cv2.getTextSize(ranking_text, config.get("text_font", cv2.FONT_HERSHEY_SIMPLEX),
                                                         config.get("text_scale", 0.6), config.get("text_thickness", 2))
        text_x = icon_center_x - text_width // 2
        text_y = frame.shape[0] - config.get("text_offset", 10)
        cv2.putText(frame, ranking_text, (text_x, text_y), config.get("text_font", cv2.FONT_HERSHEY_SIMPLEX),
                    config.get("text_scale", 0.6), config.get("text_color", (255, 255, 255)),
                    config.get("text_thickness", 2), cv2.LINE_AA)        
      
    return frame
