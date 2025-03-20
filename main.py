#Main.py

import cv2
import numpy as np
import time
import cv2.aruco as aruco

from config import (
    CAR_IMAGES, CAR_TEXT_POSITIONS, SIDEBAR_TEXT_COLORS, FONT, FONT_SCALE_SIDEBAR, FONT_SCALE_RANKING_BAR, THICKNESS, LINE_TYPE,
    COLOR_GREEN, COLOR_BLUE, COLOR_WHITE, COLOR_RED, POSITION_INDICATOR_CONFIG,
    LAP_COMPLETE_DURATION, COOLDOWN_TIME, TOTAL_LAPS,
    MARKER_REAL_WIDTH, FOCAL_LENGTH, INITIAL_SCALE_FACTOR, MIN_SCALE_FACTOR,
    RANKING_BAR_CONFIG, PATH_POINTS, PATH_WIDTH,
    FINISH_ZONE, CAMERA_INDEX, BLACK_BAR_WIDTH, CAR_TEXT_POSITIONS,
    START_TEXT, START_TEXT_POSITION, START_TEXT_FONT_SCALE, START_TEXT_COLOR, START_TEXT_THICKNESS,
    COUNTDOWN_FONT_SCALE, COUNTDOWN_COLOR, COUNTDOWN_THICKNESS, COUNTDOWN_OFFSET_X, COUNTDOWN_OFFSET_Y,
    GO_TEXT, GO_TEXT_FONT_SCALE, GO_TEXT_COLOR, GO_TEXT_THICKNESS, GO_TEXT_OFFSET_X, GO_TEXT_OFFSET_Y
)

from car import Car
from race_manager import RaceManager
from image_utils import load_image, overlay_image
from path_utils import expand_path
from ranking_bar import draw_ranking_bar
from tracking_utils import project_to_centerline

def compute_cumulative_distances(path_points):
    #Bereken de cumulatieve afstanden langs het traject.
    cum_distances = [0.0]
    for i in range(1, len(path_points)):
        p1 = np.array(path_points[i - 1], dtype=float)
        p2 = np.array(path_points[i], dtype=float)
        distance = np.linalg.norm(p2 - p1)
        cum_distances.append(cum_distances[-1] + distance)
    return cum_distances

def calculate_progress_distance(car, path_points):
    """
    Berekent de afgelegde afstand (raw progress) langs het traject voor een auto,
    zijnde de cumulatieve afstand van het eerste punt tot aan het punt op het traject
    dat het dichtst bij de auto ligt. Hier werken we in het display-systeem door BLACK_BAR_WIDTH
    op te tellen bij de x-waarde.
    """

    # Debug: Controleer de huidige coördinaten van de auto
    print(f"DEBUG: Auto {car.marker_id} positie voor progressie: x={car.x}, y={car.y}")
    
    # Bereken de progressie langs het pad
    progress_distance = project_to_centerline((car.x, car.y), path_points)

    # Debug: Controleer de berekende progressie
    print(f"DEBUG: Auto {car.marker_id} berekende progressie: {progress_distance}")
    
    # Update de progressie van de auto
    car.progress = progress_distance
    
    if car.x is None or car.y is None:
        return 0.0
    # Verander raw x naar display x: voeg de offset toe.
    car_pos = np.array([car.x, car.y], dtype=float)
    cum_distances = compute_cumulative_distances(path_points)
    best_progress = 0.0
    min_perp = float('inf')
    for i in range(len(path_points) - 1):
        A = np.array(path_points[i], dtype=float)
        B = np.array(path_points[i+1], dtype=float)
        AB = B - A
        if np.dot(AB, AB) == 0:
            continue
        t = np.dot(car_pos - A, AB) / np.dot(AB, AB)
        t_clamped = np.clip(t, 0, 1)
        P = A + t_clamped * AB
        perp_distance = np.linalg.norm(car_pos - P)
        if perp_distance < min_perp:
            min_perp = perp_distance
            segment_length = np.linalg.norm(AB)
            progress = cum_distances[i] + t_clamped * segment_length
            best_progress = progress
    return best_progress

def sort_cars_by_position(cars):
    """
    Sorteert de auto's op basis van hun afgeronde lappen en de progress (cumulatieve afstand)
    langs het traject. Er wordt een start_offset berekend aan de hand van een bekend startpunt (350,50).
    
    Finished auto's (waarbij 'finished' True is en 'final_position' is ingesteld) blijven in de volgorde
    waarin ze gefinished zijn, terwijl niet-finished auto's dynamisch worden gesorteerd op lap_count en progress.
    Uiteindelijk krijgt iedere auto een overall positie (position).
    """
    # Bereken cumulatieve afstanden langs het traject
    cum = compute_cumulative_distances(PATH_POINTS)
    total_distance = cum[-1]
    
    # Gebruik direct het startpunt in plaats van een DummyCar
    start_point = (350, 50)  # Dit is het startpunt zoals gedefinieerd in PATH_POINTS
    print(f"Startpunt voor offsetberekening: {start_point}")
    start_offset = project_to_centerline(start_point, PATH_POINTS)
    print(f"Start_offset: {start_offset}")

    # Bereken voor elke auto de progressie als haar positie bekend is
    for car in cars.values():
        if car.x is not None and car.y is not None:
            raw_progress = calculate_progress_distance(car, PATH_POINTS)
            # Trek de start_offset af en neem modulo om de progressie binnen de totale afstand te houden
            car.progress = (raw_progress - start_offset) % total_distance
        else:
            car.progress = 0  # Als er geen geldig positie is, zet progress op 0

    # Verdeel de auto's in finished en niet-finished
    finished_cars = [car for car in cars.values() if car.finished and car.final_position is not None]
    non_finished_cars = [car for car in cars.values() if not (car.finished and car.final_position is not None)]
    
    # Sorteer de finished auto's op hun final_position (kleinste waarde = eerste finish)
    finished_cars.sort(key=lambda car: car.final_position)
    
    # Sorteer de niet-finished auto's zoals eerder: op lap_count en progress (in afnemende volgorde)
    non_finished_cars.sort(key=lambda car: (car.lap_count, car.progress), reverse=True)
    
    # Combineer beide lijsten: finished auto's komen eerst
    sorted_cars = finished_cars + non_finished_cars
    
    # Wijs overall posities (rankings) toe op basis van de gesorteerde volgorde
    for idx, car in enumerate(sorted_cars):
        car.position = idx + 1  # Rangnummers beginnen bij 1

    # Debug: Print de gesorteerde volgorde en relevante info
    print("Gesorteerde auto's (position, marker_id, finished, final_position, lap_count, progress):")
    for car in sorted_cars:
        print(f"Pos {car.position}: Marker ID {car.marker_id}, Finished: {car.finished}, Final Pos: {car.final_position}, Lap Count: {car.lap_count}, Progress: {car.progress:.2f}")

    return sorted_cars

def expand_path(path_points, width):
    # Bereidt het traject (path) voor door de coördinaten in een numpy-array te zetten.
    return np.array(path_points, dtype=np.int32)

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
    
def update_car_positions(cars, frame_width, frame_height):
    """
    Bereken en update de posities voor auto-informatie op basis van het frame.

    Args:
        cars (dict): Een dictionary met Car-objecten, waarbij de key de marker_id is.
        frame_width (int): De breedte van het cameraframe.
        frame_height (int): De hoogte van het cameraframe.
    """
    for marker_id, car_key in enumerate(['blue_car', 'green_car']):
        print(f"Processing marker_id: {marker_id}")
        
        # Controleer of de marker_id in cars bestaat
        if marker_id not in cars:
            print(f"Fout: marker_id {marker_id} niet gevonden in 'cars'. Sla over.")
            continue
        
        # Haal de offsets uit de configuratie
        offsets = CAR_TEXT_POSITIONS[car_key]

        # Pas BLACK_BAR_WIDTH toe op basis van marker_id
        if marker_id == 1:  # Groene auto: links in de zijbalk
            x_lap = offsets['lap_position_offset'][0] + BLACK_BAR_WIDTH
            y_lap = offsets['lap_position_offset'][1]
            x_complete = offsets['lap_complete_position_offset'][0] + BLACK_BAR_WIDTH
            y_complete = offsets['lap_complete_position_offset'][1]
        else:  # Blauwe auto: rechts in de zijbalk
            x_lap = frame_width - offsets['lap_position_offset'][0] - BLACK_BAR_WIDTH
            y_lap = offsets['lap_position_offset'][1]
            x_complete = frame_width - offsets['lap_complete_position_offset'][0] - BLACK_BAR_WIDTH
            y_complete = offsets['lap_complete_position_offset'][1]

        # Debug: Controleer de aangepaste waarden
        print(f"marker_id {marker_id}, x_lap: {x_lap}, y_lap: {y_lap}")
        print(f"marker_id {marker_id}, x_complete: {x_complete}, y_complete: {y_complete}")
        
        # Update de posities in het respectieve Car-object
        cars[marker_id].lap_position = (x_lap, y_lap)
        cars[marker_id].lap_complete_position = (x_complete, y_complete)

def draw_text(frame, text, position, color, font_scale=1, thickness=2):
    
    #Tekent tekst op het frame.
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                font_scale, color, thickness, cv2.LINE_AA)
    
def initialize_cars():
    from config import CAR_IMAGES, SIDEBAR_TEXT_COLORS, CAR_TEXT_POSITIONS
    from image_utils import load_image
    cars = {}
    try:
        for car_key, car_config in CAR_IMAGES.items():
            car_image = load_image(car_config["path"], car_config["width"], car_config["height"])
            color = SIDEBAR_TEXT_COLORS.get(car_key, (255, 255, 255))
            car = Car(
                marker_id = len(cars),
                color = color,
                car_image = car_image,
                lap_position = CAR_TEXT_POSITIONS[car_key]["lap_position_offset"],
                lap_complete_position = CAR_TEXT_POSITIONS[car_key]["lap_complete_position_offset"],
                color_key = car_key  # Zorg dat dit argument hier wordt meegegeven
            )
            cars[len(cars)] = car
    except Exception as e:
        print(f"Fout bij het initialiseren van auto's: {e}")
    return cars

def handle_countdown(frame, race_manager, cars):
    """
    Behandelt de pre-race fase: 
     - Als de countdown nog niet gestart is, wordt het startscherm getoond.
     - Als de countdown bezig is, wordt het nummer getoond;
       bij 0 start de race en verschijnt 'GO!'.
    
    Retourneert True als we na de countdown de rest van het frame niet verder hoeven te verwerken.
    """
    if race_manager.countdown_start_time is None:
        draw_text(frame, START_TEXT, START_TEXT_POSITION,
                  START_TEXT_COLOR, START_TEXT_FONT_SCALE, START_TEXT_THICKNESS)
        return True
    else:
        countdown_number = race_manager.update_countdown()
        if countdown_number is not None:
            if countdown_number > 0:
                pos = (frame.shape[1] // 2 - COUNTDOWN_OFFSET_X,
                       frame.shape[0] // 2 + COUNTDOWN_OFFSET_Y)
                draw_text(frame, str(countdown_number), pos,
                          COUNTDOWN_COLOR, COUNTDOWN_FONT_SCALE, COUNTDOWN_THICKNESS)
            else:
                pos = (frame.shape[1] // 2 - GO_TEXT_OFFSET_X,
                       frame.shape[0] // 2 + GO_TEXT_OFFSET_Y)
                draw_text(frame, GO_TEXT, pos,
                          GO_TEXT_COLOR, GO_TEXT_FONT_SCALE, GO_TEXT_THICKNESS)
                if not race_manager.race_started:
                    race_manager.start_race()
                    for car in cars.values():
                        car.last_lap_time = race_manager.race_start_time
            return True  # We verwerken niks verder tijdens de countdown
    return False

def process_detected_markers(new_frame, cars, parameters, aruco_dict, race_manager):
    """
    Detecteert ArUco-markers in new_frame en verwerkt ze.
    """
    gray = cv2.cvtColor(new_frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    # Debug: Bekijk de gedetecteerde ArUco-corners en IDs
    print(f"Detected ArUco corners: {corners}")
    print(f"Detected ArUco IDs: {ids}")
    
    if ids is not None and len(ids) > 0:
        process_markers(cars, corners, ids, new_frame, race_manager)


def update_and_draw_overlays(frame, cars, race_manager):
    """
    Update de progress van elke auto (langs de centerline), berekent
    de ranking en tekent vervolgens de auto-informatie overlays, 
    inclusief de auto-afbeeldingen en de rangindicator, op basis van de display-coördinaten.
    
    Hierbij worden de coördinaten gebruikt die eerder in process_frame
    als car.display_x en car.display_y zijn ingesteld, zodat de overlays niet gespiegeld worden.
    
    Returns:
        frame (numpy.ndarray): Het frame met toegevoegde overlays.
    """
    sorted_cars = sort_cars_by_position(cars)
    current_time = time.time()
    display_car_info(cars, frame, current_time, race_manager)
    frame = draw_ranking_bar(frame, sorted_cars, RANKING_BAR_CONFIG)

    # teken de auto-afbeeldingen en rangindicatoren met de display-coördinaten,
    for car in sorted_cars:
        if hasattr(car, "display_x") and hasattr(car, "display_y"):
            # Gebruik car.display_x en car.display_y voor de plaatsing van de auto-afbeelding
            overlay_image(frame, car.car_image, car.display_x, car.display_y, car.scale_factor)
            overlay_position_indicator(frame, car)
    
    return frame

def process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path):
    """
    Verwerkt een frame voor de race en bouwt een definitieve composiet op uit twee lagen:
      - Achtergrondlaag: het oorspronkelijke camerabeeld wordt gespiegeld.
      - Overlaylaag: alle overlays (traject, finish-zone, auto-informatie, indicatoren, "GO!"-tekst)
         worden getekend in de originele oriëntatie op basis van display-coördinaten.
    
    Uiteindelijk wordt in de cameraregion van de composiet de gespiegelde achtergrond vervangen
    door de overlaylaag, zodat de overlays in originele (niet-spiegelde) oriëntatie verschijnen.
    """
    # Maak een basiscopy van het originele frame voor de detectie en overlays
    base_frame = frame.copy()
    frame_height, frame_width = base_frame.shape[:2]
    
    # ArUco-detectie op het originele, ongespiegelde beeld.
    gray = cv2.cvtColor(base_frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    if ids is not None and len(ids) > 0:
        process_markers(cars, corners, ids, base_frame, race_manager)
    
    # Maak de composiet: extra ruimte voor de zwarte balken en ranking bar.
    ranking_bar_height = RANKING_BAR_CONFIG['ranking_bar_height']
    composite_width = frame_width + 2 * BLACK_BAR_WIDTH
    composite_height = frame_height + ranking_bar_height
    new_frame = np.zeros((composite_width, composite_height, 3), dtype=np.uint8)  # Let op: volgorde (hoogte, breedte, 3)
    new_frame = np.zeros((composite_height, composite_width, 3), dtype=np.uint8)
    
    # Definieer de cameraregion in het nieuwe canvas.
    cam_region = (slice(0, frame_height), slice(BLACK_BAR_WIDTH, BLACK_BAR_WIDTH + frame_width))
    new_frame[cam_region] = base_frame  # Plaats het originele beeld eerst.
    
    if not race_manager.race_started:
        handle_countdown(new_frame, race_manager, cars)
        return new_frame
    
    # Werk de cameraregion (base_frame updates) bij.
    new_frame[cam_region] = base_frame
    
    # Teken het traject en de finish-zone op new_frame.
    draw_race_track(new_frame, expanded_path)
    draw_finish_zone(new_frame)
    
    # Update de auto-posities relatief aan de composiet.
    update_car_positions(cars, composite_width, composite_height)
    
    # Bereken voor iedere auto de display-coördinaten: raw + offset.
    # Let op: alleen bij geldige (niet-None) coördinaten
    for car in cars.values():
        if car.x is not None and car.y is not None:
            # Hier gebruik je eventueel nog een offset; als dat niet nodig is, gebruik alleen de basispositie.
            car.display_x = car.x
            car.display_y = car.y
        else:
            print(f"Warning: Car {car.marker_id} heeft geen geldige positie (x={car.x}, y={car.y}); overlay overslaan.")
    
    # Teken als laatste alle overlays, inclusief de auto-afbeeldingen en indicatoren.
    new_frame = update_and_draw_overlays(new_frame, cars, race_manager)
    
    # Indien de race net gestart is, teken "GO!" in de cameraregion.
    if race_manager.race_started and (time.time() - race_manager.race_start_time < 1):
        pos = (BLACK_BAR_WIDTH + frame_width//2 - GO_TEXT_OFFSET_X,
               frame_height//2 + GO_TEXT_OFFSET_Y)
        draw_text(new_frame, GO_TEXT, pos, GO_TEXT_COLOR, GO_TEXT_FONT_SCALE, GO_TEXT_THICKNESS)
    
    return new_frame

    
def process_markers(cars, corners, ids, new_frame, race_manager):
    """
    Verwerkt de gedetecteerde ArUco-markers:
      - Tekent de markers in het frame.
      - Berekent het centrum (x, y) van elke marker.
      - Controleert of een marker binnen de finish-zone ligt en verhoogt zo nodig de lap.
      - Berekent een schaalfactor op basis van de marker grootte en update de positie van de auto.
      - Overlayt de auto-afbeelding op het frame.
    """
    # Teken alle gedetecteerde markers
    cv2.aruco.drawDetectedMarkers(new_frame, corners, ids)
    print(f"Detected IDs: {ids}")
    print(f"Detected Corners: {corners}")
    
    # Bereken de finish-zone als een polygon
    finish_box = cv2.boxPoints(FINISH_ZONE)
    finish_box = np.int32(finish_box)
    finish_box[:, 0] -= BLACK_BAR_WIDTH
    print(f"Finish box (na BLACK_BAR_WIDTH-correctie): {finish_box}")
    
    for i, marker_id in enumerate(ids.flatten()):
        # Controleer of deze marker overeenkomt met een auto
        if marker_id not in cars:
            print(f"Marker ID {marker_id} komt niet overeen met een auto.")
            continue

        car = cars[marker_id]
        
        # Bereken het centrum van de marker
        x_center = int(np.mean(corners[i][0][:, 0]))
        y_center = int(np.mean(corners[i][0][:, 1]))
        
        # Pas correctie toe om positie aan te passen
        x_offset = 350 - 150  # Verwachte waarde - geregistreerde waarde
        y_offset = 50 - 50    # Verwachte waarde - geregistreerde waarde
        adjusted_x = x_center + x_offset
        adjusted_y = y_center + y_offset
        print(f"Marker ID {marker_id}: Aangepaste positie: x = {adjusted_x}, y = {adjusted_y}")
        
        # Controleer of de marker binnen de finish-zone ligt
        if cv2.pointPolygonTest(finish_box, (x_center, y_center), False) >= 0:
            if not car.finished:
                current_time = time.time()
                if current_time - car.last_lap_time > race_manager.cooldown_time:
                    print(f"Marker ID {marker_id} passeert de finish.")
                    car.increment_lap(current_time, TOTAL_LAPS, race_manager)
                else:
                    print(f"Marker ID {marker_id} is in cooldown en kan de lap niet verhogen.")
        
        # Bepaal de grootte van de marker om de afstand en de schaalfactor te berekenen
        width = np.linalg.norm(corners[i][0][0] - corners[i][0][1])
        height = np.linalg.norm(corners[i][0][0] - corners[i][0][3])
        marker_size = (width + height) / 2
        distance = (MARKER_REAL_WIDTH * FOCAL_LENGTH) / marker_size
        scale_factor = max(INITIAL_SCALE_FACTOR * (1 / distance), MIN_SCALE_FACTOR)
        print(f"Marker ID {marker_id}: width = {width}, height = {height}, marker_size = {marker_size}, distance = {distance}, scale_factor = {scale_factor}")
        
        # Update de positie en schaal van de auto
        car.update_position(adjusted_x, adjusted_y, scale_factor)
        print(f"Auto {marker_id} bijgewerkte positie: x = {car.x}, y = {car.y}, scale_factor = {car.scale_factor}")
        #overlay_image(new_frame, car.car_image, adjusted_x, adjusted_y, scale_factor)
            
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

def display_car_info(cars, frame, current_time, race_manager):
    """
    Toont informatie over elke auto op het frame. Dit omvat:
      - Ronde-informatie: de huidige lap of of de auto 'Finished' is
      - Lap Complete melding en de lap-tijd (indien recent voltooid)
      - Totale racetijd en de snelste lap
      - De overlay van de positie-indicator op de auto
    """
    for car in cars.values():
        if not car.lap_position or not car.lap_complete_position:
            print(f"Fout: lap_position of lap_complete_position ontbreekt voor auto met marker_id {car.marker_id}")
            continue

        color = SIDEBAR_TEXT_COLORS.get(car.color_key, (255, 255, 255))  # Standaardkleur wit
        pos = car.lap_position  # Positie voor de basis tekst (zijbalk)
        lap_complete_pos = car.lap_complete_position
        lap_time_diff = current_time - car.lap_text_start_time

        # Als de lap net voltooid is, toon "Lap Complete" en de lap-tijd
        if lap_time_diff < LAP_COMPLETE_DURATION:
            draw_text(frame, "Lap Complete", lap_complete_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
            if car.lap_times:
                last_lap_time = car.lap_times[-1]
                if last_lap_time > 0:
                    minutes, seconds = divmod(last_lap_time, 60)
                    lap_time_str = f"{int(minutes)}m {seconds:.2f}s"
                    label_pos = (lap_complete_pos[0], lap_complete_pos[1] + 30)
                    draw_text(frame, "Lap Time:", label_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
                    value_pos = (label_pos[0], label_pos[1] + 25)
                    draw_text(frame, lap_time_str, value_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)

        # Bereken de totale racetijd als de race gestart is
        if race_manager.race_start_time:
            if car.finished and car.finish_time is not None:
                total_race_time = car.finish_time - race_manager.race_start_time
            else:
                total_race_time = current_time - race_manager.race_start_time
            total_minutes, total_seconds = divmod(total_race_time, 60)
            total_time_str = f"{int(total_minutes)}m {total_seconds:.2f}s"
        else:
            total_time_str = "N/A"

        # Bepaal de snelste lap
        best_lap_time = car.get_best_lap_time()
        if best_lap_time:
            best_minutes, best_seconds = divmod(best_lap_time, 60)
            best_lap_str = f"{int(best_minutes)}m {best_seconds:.2f}s"
        else:
            best_lap_str = "N/A"

        # Toon de ronde-informatie: als de auto finished is, toon "Finished",
        # anders toon de huidige lap (bijvoorbeeld "Lap 2")
        if car.finished:
            draw_text(frame, "Finished", pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
        else:
            lap_str = f"Lap {car.lap_count + 1}"
            draw_text(frame, lap_str, pos, color, FONT_SCALE_SIDEBAR, THICKNESS)

        # Positioneer de aanvullende informatie onder de basis positie
        total_label_pos = (pos[0], pos[1] + 35)
        total_value_pos = (pos[0], total_label_pos[1] + 25)
        best_label_pos = (pos[0], total_value_pos[1] + 35)
        best_value_pos = (pos[0], best_label_pos[1] + 25)

        draw_text(frame, "Total Time:", total_label_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
        draw_text(frame, total_time_str, total_value_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
        draw_text(frame, "Fastest Lap:", best_label_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)
        draw_text(frame, best_lap_str, best_value_pos, color, FONT_SCALE_SIDEBAR, THICKNESS)

        # Voeg de positie-indicator toe aan het frame
        overlay_position_indicator(frame, car)

def main():
    # Print de gebruikte OpenCV-versie
    print(f"OpenCV-versie: {cv2.__version__}")

    # Open de camera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Kan de camera niet openen.")
        return

    # Initialiseer auto's en de race manager
    cars = initialize_cars()
    for marker_id, car in cars.items():
        print(f"Car {marker_id}: color_key = {car.color_key}, color = {car.color}")

    race_manager = RaceManager()

    # Definieer het ArUco-dictionary en de detectieparameters
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()

    # Maak het uitgezette pad (expanded_path) voor het parcours
    expanded_path = expand_path(PATH_POINTS, width=PATH_WIDTH)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Frame error, probeer opnieuw...")
            continue

        # Verwerk het frame: dit omvat het tekenen van het parcours, finish-zone, countdown, marker-detectie, en overlays
        processed_frame = process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path)

        # Toon het verwerkte frame
        cv2.imshow("ArUco Auto Tracken met Ronde Detectie", processed_frame)

        # Afhandeling van toetsen:
        key = cv2.waitKey(1) & 0xFF
        if key in [ord('q'), 27]:
            break
        elif key in [13, 10]:  # Enter toets
            if not race_manager.race_started and race_manager.countdown_start_time is None:
                race_manager.start_countdown()
        elif key == ord('r'):
            race_manager.reset_race()
            for car in cars.values():
                car.reset()

    # Zorg ervoor dat de camera netjes wordt vrijgegeven en vensters worden gesloten.
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
