#overlay_utils
import cv2
import numpy as np
import time

from config import *
from race_sorting import sort_cars_by_position
from ranking_bar import draw_ranking_bar
from image_utils import overlay_image

def draw_race_track(frame, path_points):
    # Tekent het traject (de centerline) op het frame.
    pts = np.array(path_points, dtype=np.int32).reshape((-1, 1, 2))
    # Teken de polyline; isClosed=False geeft aan dat de lijn niet gesloten wordt.
    cv2.polylines(frame, [pts], isClosed=False, color=(0, 0, 255), thickness=PATH_WIDTH)
    
def draw_finish_zone(frame):
    """
    Tekent de finish-zone als een rotated rectangle op het frame.
    """
    finish_box = cv2.boxPoints(FINISH_ZONE)
    finish_box = finish_box.astype(np.int32)
    cv2.polylines(frame, [finish_box], True, (255, 255, 0), 2)
    
def draw_checkpoint_zone(frame):
    """
    Tekent de checkpoint-zone als een rotated rectangle op het frame.
    """
    checkpoint_box = cv2.boxPoints(CHECKPOINT_ZONE)
    checkpoint_box = checkpoint_box.astype(np.int32)
    cv2.polylines(frame, [checkpoint_box], True, (0, 255, 255), 2)  # Gele kleur voor checkpoint
    
def draw_text(frame, text, position, color, font_scale=1, thickness=2):
    
    #Tekent tekst op het frame.
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                font_scale, color, thickness, cv2.LINE_AA)

def overlay_position_indicator(frame, car):
    """
    Tekent een positie-indicator op of nabij de auto-afbeelding, zodat zowel
    het rangnummer als de progress zichtbaar zijn. De instellingen (grootte, kleur, positie)
    worden via de configuratie in config.py ingesteld.
    """
    # Gebruik de display-coördinaten als die beschikbaar zijn, anders de ruwe coördinaten.
    x = car.display_x if hasattr(car, "display_x") and car.display_x is not None else car.x
    y = car.display_y if hasattr(car, "display_y") and car.display_y is not None else car.y

    if x is None or y is None:
        return  # Niets doen als er geen geldige positie is.

    # Haal de instellingen op uit de configuratie
    radius_factor = POSITION_INDICATOR_CONFIG.get("radius_factor", 30)
    offset_x, offset_y = POSITION_INDICATOR_CONFIG.get("offset", (0, -150))
    text_scale_base = POSITION_INDICATOR_CONFIG.get("text_scale", 1.0)
    text_color = POSITION_INDICATOR_CONFIG.get("text_color", (0,0,0))
    thickness = POSITION_INDICATOR_CONFIG.get("line_thickness", 2)
    pos_colors = POSITION_INDICATOR_CONFIG.get("colors", {})

    # Bepaal de indicatorstraal; deze is afhankelijk van de schaalfactor van de auto.
    indicator_radius = int(radius_factor * car.scale_factor)
    
    # Kies de kleur op basis van de rangpositie (car.position)
    indicator_color = pos_colors.get(car.position, pos_colors.get("default", (255,255,255)))
    
    # Bereken het centrum van de indicator. We passen de configuratie-offset toe.
    indicator_center = (
        int(x + offset_x),
        int(y + offset_y * car.scale_factor)
    )
    
    # Teken een ingevulde cirkel voor de indicator.
    cv2.circle(frame, indicator_center, indicator_radius, indicator_color, -1)
    
    # Bereken de rangtekst en teken deze gecentreerd in de indicator.
    rank_text = str(car.position)
    font_scale = text_scale_base * car.scale_factor
    (text_width, text_height), _ = cv2.getTextSize(rank_text, FONT, font_scale, thickness)
    text_x = indicator_center[0] - text_width // 2
    text_y = indicator_center[1] + text_height // 2
    cv2.putText(frame, rank_text, (text_x, text_y), FONT, font_scale, text_color, thickness, LINE_TYPE)
    
    # Debug: Print de progress voor de auto.
    print(f"Car {car.marker_id} progress: {car.progress:.1f}")
    
    return frame

import cv2

def draw_final_ranking_overlay(frame, sorted_cars):
    """
    Teken een semi-transparante overlay in het midden van het frame met het eindklassement.

    Args:
        frame (numpy.ndarray): Het uiteindelijke frame waarop de overlay getekend wordt.
        sorted_cars (list): Lijst met gesorteerde Car-objecten op basis van finishvolgorde.
        
    Returns:
        numpy.ndarray: Het frame met de finale ranking-overlay.
    """
    # Haal de configuratieparameters op uit FINAL_OVERLAY_CONFIG.
    overlay_color = FINAL_OVERLAY_CONFIG["overlay_color"]
    alpha = FINAL_OVERLAY_CONFIG["alpha"]
    width_ratio = FINAL_OVERLAY_CONFIG["width_ratio"]
    height_ratio = FINAL_OVERLAY_CONFIG["height_ratio"]
    margin = FINAL_OVERLAY_CONFIG["margin"]
    title_text = FINAL_OVERLAY_CONFIG["title_text"]
    title_font_scale = FINAL_OVERLAY_CONFIG["title_font_scale"]
    title_thickness = FINAL_OVERLAY_CONFIG["title_thickness"]
    text_font = FINAL_OVERLAY_CONFIG["text_font"]
    text_font_scale = FINAL_OVERLAY_CONFIG["text_font_scale"]
    text_thickness = FINAL_OVERLAY_CONFIG["text_thickness"]
    text_color = FINAL_OVERLAY_CONFIG["text_color"]

    # Maak een overlay-kopie van het frame
    overlay = frame.copy()
    frame_h, frame_w = frame.shape[:2]
    
    # Bepaal de grootte van het overlay-venster
    overlay_w = int(frame_w * width_ratio)
    overlay_h = int(frame_h * height_ratio)
    
    # Centreer het overlay
    top_left_x = (frame_w - overlay_w) // 2
    top_left_y = (frame_h - overlay_h) // 2
    
    # Teken een gevuld rechthoekig overlay
    cv2.rectangle(overlay, (top_left_x, top_left_y),
                  (top_left_x + overlay_w, top_left_y + overlay_h),
                  overlay_color, -1)
    
    # Combineer de overlay en het originele frame met de gegeven alpha (transparantie)
    output = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
    
    # Teken de titel in het overlay
    title_size, _ = cv2.getTextSize(title_text, text_font, title_font_scale, title_thickness)
    title_x = top_left_x + (overlay_w - title_size[0]) // 2
    title_y = top_left_y + title_size[1] + margin
    cv2.putText(output, title_text, (title_x, title_y), text_font, title_font_scale, text_color, title_thickness, cv2.LINE_AA)
    
    # Stel de startpositie voor de tekstregels binnen het overlay in
    start_y = title_y + margin + 20  # marge onder de titel
    line_height = 30  # hoogte tussen de tekstregels (pas aan indien nodig)
    text_x = top_left_x + margin

    # Voor elke auto in de gesorteerde lijst: teken een regel met ranking en username.
    for i, car in enumerate(sorted_cars):
        # Haal de username direct uit het Car-object, gebruik fallback als deze niet is ingesteld.
        username = car.username if car.username is not None else f"Car {car.marker_id}"
        rank_text = f"{i+1}. {username}"
        pos = (text_x, start_y + i * line_height)
        cv2.putText(output, rank_text, pos, text_font, text_font_scale, text_color, text_thickness, cv2.LINE_AA)

    return output

def update_and_draw_overlays(frame, cars, race_manager):
    """
    Update de progress van elke auto (langs de centerline), berekent de ranking en tekent de
    auto-informatie overlays op basis van de display-coördinaten die eerder in process_frame 
    (bijv. car.display_x en car.display_y) zijn ingesteld. 
    
    Omdat alle auto-informatie nu dynamisch in de Car-objecten zit (via CAR_CONFIG),
    hoeft deze functie niet aangepast te worden als je een auto toevoegt of verwijdert.

    Returns:
        frame (numpy.ndarray): Het originele frame met alle overlays toegevoegd.
    """
    # Sorteer de auto's op basis van hun progress (deze functie is verondersteld al dynamisch de Car objecten te verwerken)
    sorted_cars = sort_cars_by_position(cars)
    current_time = time.time()
    
    # Werk de auto-informatie bij en teken deze overlay (zoals username, lap-tijd, enz.)
    display_car_info(cars, frame, current_time, race_manager)
    
    # Teken de ranking bar (deze functie gebruikt nu de dynamisch gesorteerde auto's en RANKING_BAR_CONFIG)
    frame = draw_ranking_bar(frame, sorted_cars, RANKING_BAR_CONFIG)
    
    # Voor elke auto: teken de auto-afbeelding en de position indicator op basis van de display-coördinaten die eerder zijn vastgesteld.
    for car in sorted_cars:
        if car.x is not None and car.y is not None:  # Controleer of de marker gedetecteerd is
            overlay_image(frame, car.car_image, car.x, car.y, car.scale_factor)
            overlay_position_indicator(frame, car)
        else:
            print(f"Auto {car.marker_id} heeft nog geen geldige positie. Overslaan.")
    
    return frame

def display_car_info(cars, frame, current_time, race_manager):
    """
    Toont informatie over elke auto op het frame. Dit omvat:
      - De gebruikersnaam van de auto (boven de overlay-tekst).
      - Huidige lap-info: of de auto "Finished" is, of welke lap actief is.
      - Totale racetijd en de snelste lap.
      - Eventueel een positie-indicator.
    """
    for car in cars.values():
        if not car.lap_position or not car.lap_complete_position:
            print(f"Fout: lap_position of lap_complete_position ontbreekt voor auto met marker_id {car.marker_id}")
            continue

        # Gebruik de kleur die is ingesteld via de initialisatie (bijv. via settings["sidebar_text_color"])
        color = car.color  
        username = car.username if car.username is not None else car.color_key.capitalize()

        pos = car.lap_position  # Basispositie voor overlay-teksten

        # Teken de gebruikersnaam (30 pixels boven de basispositie)
        username_pos = (pos[0], pos[1] - 30)
        draw_text(frame, username, username_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)

        # Controleer of de race is gestart
        if not race_manager.race_started:
            total_time_str = "0.000s"
            best_lap_str = "N/A"
            lap_str = "Lap 1"
        else:
            lap_time_diff = current_time - car.lap_text_start_time

            # Als de lap net is voltooid, toon "Lap Complete" en de lap-tijd
            if lap_time_diff < LAP_COMPLETE_DURATION:
                draw_text(frame, "Lap Complete", car.lap_complete_position, color, FONT_SCALE_SIDEBAR, THICKNESS)
                if car.lap_times:
                    last_lap_time = car.lap_times[-1]
                    if last_lap_time > 0:
                        minutes, seconds = divmod(last_lap_time, 60)
                        lap_time_str = f"{int(minutes)}m {seconds:.2f}s"
                        label_pos = (car.lap_complete_position[0], car.lap_complete_position[1] + 30)
                        draw_text(frame, "Lap Time:", label_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
                        value_pos = (label_pos[0], label_pos[1] + 25)
                        draw_text(frame, lap_time_str, value_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)

            # Bereken en formatteer de totale tijd
            if car.finished and car.finish_time is not None:
                total_race_time = car.finish_time - race_manager.race_start_time
            else:
                total_race_time = current_time - race_manager.race_start_time
            total_minutes, total_seconds = divmod(total_race_time, 60)
            total_time_str = f"{int(total_minutes)}m {total_seconds:.2f}s"

            # Bereken en formatteer de snelste ronde
            best_lap_time = car.get_best_lap_time()
            if best_lap_time:
                best_minutes, best_seconds = divmod(best_lap_time, 60)
                best_lap_str = f"{int(best_minutes)}m {best_seconds:.2f}s"
            else:
                best_lap_str = "N/A"

            # Toon de huidige ronde
            if car.finished:
                draw_text(frame, "Finished", pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
            else:
                lap_str = f"Lap {car.lap_count + 1}"

        # Teken tijd- en ronde-informatie
        total_label_pos = (pos[0], pos[1] + 35)
        total_value_pos = (pos[0], total_label_pos[1] + 25)
        best_label_pos = (pos[0], total_value_pos[1] + 35)
        best_value_pos = (pos[0], best_label_pos[1] + 25)

        draw_text(frame, lap_str, pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
        draw_text(frame, "Total Time:", total_label_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
        draw_text(frame, total_time_str, total_value_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
        draw_text(frame, "Fastest Lap:", best_label_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
        draw_text(frame, best_lap_str, best_value_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)

        # Teken de positie-indicator
        overlay_position_indicator(frame, car)