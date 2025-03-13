import cv2
import numpy as np
import time
import cv2.aruco as aruco

from config import (
    FONT, FONT_SCALE_SIDEBAR, FONT_SCALE_RANKING_BAR, THICKNESS, LINE_TYPE,
    COLOR_GREEN, COLOR_BLUE, COLOR_WHITE, COLOR_RED,
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
from utils import overlay_image
from image_utils import load_image
from path_utils import expand_path
from ranking_bar import draw_ranking_bar
from tracking_utils import project_to_centerline

def compute_cumulative_distances(path_points):
    """
    Bereken de cumulatieve afstanden langs het traject.
    Args:
        path_points (list of tuple): Een lijst met (x, y)-coördinaten (bijvoorbeeld PATH_POINTS).
    Returns:
        list: Een lijst van cumulatieve afstanden, beginnend met 0.0.
    """
    cum_distances = [0.0]
    for i in range(1, len(path_points)):
        p1 = np.array(path_points[i-1], dtype=float)
        p2 = np.array(path_points[i], dtype=float)
        distance = np.linalg.norm(p2 - p1)
        cum_distances.append(cum_distances[-1] + distance)
    return cum_distances

def calculate_progress_distance(car, path_points):
    """
    Berekent de afgelegde afstand langs het traject voor een auto.
    De functie projecteert de positie van de auto op elk segment van PATH_POINTS
    en kiest het segment waarbij de loodrechte afstand minimaal is. De progress wordt
    dan de cumulatieve afstand vanaf het startpunt tot het projectiepunt.
    
    Args:
        car: Het Car-object (met attributen car.x en car.y).
        path_points: De lijst van (x, y)-punten (bijv. PATH_POINTS).
    Returns:
        float: De afgelegde afstand (progress) vanaf het startpunt.
    """
    
    if car.x is None or car.y is None:
        return 0.0
    # Gebruik de display-coördinaten: voeg de BLACK_BAR_WIDTH toe.
    car_pos = np.array([car.x + BLACK_BAR_WIDTH, car.y], dtype=float)
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
    Sorteert de auto's op basis van hun afgeronde lappen en de afgelegde afstand (progress) langs het traject.
    De progress wordt berekend als de werkelijke cumulatieve afstand en vervolgens herstart (wrapt)
    via een modulo met de totale laplengte.
    
    Args:
        cars (dict): Dictionary met Car-objecten.
    Returns:
        list: Een gesorteerde lijst van Car-objecten. Ook wordt elk Car-object voorzien van 'position'.
    """
    cum_dist = compute_cumulative_distances(PATH_POINTS)
    total_distance = cum_dist[-1]
    for car in cars.values():
        raw_progress = calculate_progress_distance(car, PATH_POINTS)
        car.progress = raw_progress % total_distance  # Wrap progress zodat bij finish het opnieuw begint.
    sorted_cars = sorted(cars.values(), key=lambda car: (car.lap_count, car.progress), reverse=True)
    for idx, car in enumerate(sorted_cars):
        car.position = idx + 1
    return sorted_cars

def draw_text(frame, text, position, color, font_scale=1, thickness=2):
    
    #Tekent tekst op het frame.
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                font_scale, color, thickness, cv2.LINE_AA)

def initialize_cars():
    """
    Initialiseert de auto's met hun eigenschappen.
    Returns:
        dict: Een dictionary met Car-objecten.
    """
    try:
        # Laad de auto-afbeeldingen
        car_images = {
            "green": load_image(r'D:\werk\warrior events\groene_auto.png', width=640, height=480),
            "blue": load_image(r'D:\werk\warrior events\blauwe_auto.png', width=640, height=480)
        }

        # Initialiseer auto's
        cars = {
            0: Car(marker_id=0, color=COLOR_BLUE, car_image=car_images["blue"],
                   lap_position=None, lap_complete_position=None),
            1: Car(marker_id=1, color=COLOR_GREEN, car_image=car_images["green"],
                   lap_position=None, lap_complete_position=None)
        }
        return cars
    
    except FileNotFoundError as e:
        print(f"Fout bij het laden van auto-afbeeldingen: {e}")
        return {}


def update_car_positions(cars, frame_width, frame_height):
    """
    Bereken en update de posities voor auto-informatie op basis van het frame.
    """
    # Overloop de auto's met hun respectievelijke configuraties
    for marker_id, car_key in enumerate(['blue_car', 'green_car']):
        offsets = CAR_TEXT_POSITIONS[car_key]

        if marker_id == 1:  # Groene auto: links in de zijbalk
            x_lap = BLACK_BAR_WIDTH - offsets['lap_position_offset'][0]
            y_lap = offsets['lap_position_offset'][1]
            x_complete = BLACK_BAR_WIDTH - offsets['lap_complete_position_offset'][0]
            y_complete = offsets['lap_complete_position_offset'][1]
        else:  # Blauwe auto: rechts in de zijbalk
            x_lap = frame_width - BLACK_BAR_WIDTH + offsets['lap_position_offset'][0]
            y_lap = offsets['lap_position_offset'][1]
            x_complete = frame_width - BLACK_BAR_WIDTH + offsets['lap_complete_position_offset'][0]
            y_complete = offsets['lap_complete_position_offset'][1]
        
        # Update de posities in het respectieve Car-object
        cars[marker_id].lap_position = (x_lap, y_lap)
        cars[marker_id].lap_complete_position = (x_complete, y_complete)

def sort_cars_by_position(cars):
    """
    Sorteert de auto's op basis van hun afgeronde lappen en de afgelegde trajectafstand.
    
    De progress wordt berekend als de cumulatieve afstand langs PATH_POINTS tot het punt waarop
    de auto het dichtst is. Daarna worden de auto's gesorteerd op (lap_count, progress) (beide aflopend).
    De positie in de race wordt bijgewerkt in elk Car-object.
    
    Args:
        cars (dict): Dictionary met Car-objecten.
    
    Returns:
        list: Een gesorteerde lijst van Car-objecten.
    """
    # Gebruik de globale PATH_POINTS (die je in config.py hebt staan)
    for car in cars.values():
        car.progress = calculate_progress_distance(car, PATH_POINTS)
    
    sorted_cars = sorted(cars.values(), key=lambda car: (car.lap_count, car.progress), reverse=True)
    
    for idx, car in enumerate(sorted_cars):
        car.position = idx + 1
    return sorted_cars

def draw_race_track(frame, expanded_path):
    """
    Tekent het parcours op het frame.
    """
    cv2.fillPoly(frame, [expanded_path], COLOR_RED)

def draw_finish_zone(frame):
    """
    Tekent de finish-zone als een rotated rectangle op het frame.
    """
    finish_box = cv2.boxPoints(FINISH_ZONE)
    finish_box = finish_box.astype(np.int32)
    cv2.polylines(frame, [finish_box], True, (255, 255, 0), 2)

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
    # Update progress voor elke auto (bv. via project_to_centerline)
    for car in cars.values():
        if car.x is not None and car.y is not None:
            progress = project_to_centerline((car.x, car.y), PATH_POINTS)
            car.progress = progress
            # Debugline uitgeschakeld: print progress niet op het scherm.
            # cv2.putText(frame, f"P: {progress:.1f}", (car.x, car.y - 20),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    # Sorteer de auto's op basis van lap en progress en update hun positie
    sorted_cars = sort_cars_by_position(cars)

    # Update overige auto-informatie overlays (zoals ronde tijden, totaal tijd, etc.)
    current_time = time.time()
    display_car_info(cars, frame, current_time, race_manager)
    
    # Teken de ranking bar
    frame = draw_ranking_bar(frame, sorted_cars, RANKING_BAR_CONFIG)

    # Als laatste, teken de auto-afbeeldingen en rangindicatoren met de display-coördinaten,
    # zodat deze bovenop alle andere overlays komen.
    for car in sorted_cars:
        if hasattr(car, "display_x") and hasattr(car, "display_y"):
            # Gebruik car.display_x en car.display_y voor de plaatsing van de auto-afbeelding
            overlay_image(frame, car.car_image, car.display_x, car.display_y, car.scale_factor)
            overlay_position_indicator(frame, car)
    
    return frame

def process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path):
    """
    Verwerkt één frame voor de race:
      - Maakt een nieuw frame met extra ruimte voor zwarte balken en ranking bar.
      - Voert, indien de race gestart is, de ArUco-detectie en overlay-trekkingen uit.
      - Als de race nog niet gestart is, worden alleen de zwarte balken (en eventueel een countdown) getekend.
      
    Resultaat: De auto-afbeelding(en) komen als laatste laag getekend bovenop het pad.
    """
    # 1. Kopieer het originele frame voor verwerking.
    base_frame = frame.copy()
    frame_height, frame_width = base_frame.shape[:2]
    
    # Voer ArUco-detectie uit op base_frame (ongeflipte versie).
    gray = cv2.cvtColor(base_frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    if ids is not None and len(ids) > 0:
        process_markers(cars, corners, ids, base_frame, race_manager)
    
    # 2. Bepaal de uiteindelijke canvas-afmetingen met extra balken.
    ranking_bar_height = RANKING_BAR_CONFIG['ranking_bar_height']
    composite_width = frame_width + 2 * BLACK_BAR_WIDTH
    composite_height = frame_height + ranking_bar_height
    new_frame = np.zeros((composite_height, composite_width, 3), dtype=np.uint8)
    
    # 3. Plaats het originele beeld (base_frame) in het centrale gebied van new_frame.
    new_frame[0:frame_height, BLACK_BAR_WIDTH:BLACK_BAR_WIDTH+frame_width] = base_frame
    
    # 4. Indien de race nog niet gestart is, teken eventueel countdown en geef new_frame terug.
    if not race_manager.race_started:
        handle_countdown(new_frame, race_manager, cars)
        return new_frame
    
    # 5. Werk new_frame bij met de updates uit base_frame (bijv. auto-posities).
    new_frame[0:frame_height, BLACK_BAR_WIDTH:BLACK_BAR_WIDTH+frame_width] = base_frame
    
    # 6. Teken het pad en de finish-zone op new_frame.
    draw_race_track(new_frame, expanded_path)
    draw_finish_zone(new_frame)
    
    # 7. Update de auto-positie-informatie afhankelijk van de nieuwe afmetingen.
    update_car_positions(cars, composite_width, composite_height)
    
    # 8. Pas de display-coördinaten voor de auto's toe zodat de overlays niet gespiegeld worden.
    for car in cars.values():
        if car.x is not None and car.y is not None:
            car.display_x = BLACK_BAR_WIDTH + car.x
            car.display_y = car.y
    
    # 9. Als laatste, teken alle overige overlays en met name de auto-afbeeldingen bovenop het pad.
    new_frame = update_and_draw_overlays(new_frame, cars, race_manager)
    
    # 10. Als de race net is gestart (minder dan 1 seconde), teken dan "GO!" op new_frame.
    if race_manager.race_started and (time.time() - race_manager.race_start_time < 1):
        pos = (BLACK_BAR_WIDTH + frame_width//2 - GO_TEXT_OFFSET_X, frame_height//2 + GO_TEXT_OFFSET_Y)
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
    
    Args:
        cars (dict): Dictionary met Car-objecten.
        corners (list): Lijst met de hoekcoördinaten per gedetecteerde marker.
        ids (numpy.ndarray): Array met de marker IDs.
        new_frame (numpy.ndarray): Het huidige videoframe waarop getekend wordt.
        race_manager: Het race_manager object dat cooldown en andere race-gerelateerde zaken beheert.
    """
    # Teken alle gedetecteerde markers
    cv2.aruco.drawDetectedMarkers(new_frame, corners, ids)
    
    # Bereken de finish-zone als een polygon
    finish_box = cv2.boxPoints(FINISH_ZONE)
    finish_box = np.int32(finish_box)
    finish_box[:, 0] -= BLACK_BAR_WIDTH
    
    for i, marker_id in enumerate(ids.flatten()):
        # Controleer of deze marker overeenkomt met een auto
        if marker_id not in cars:
            continue

        car = cars[marker_id]
        # Bereken het centrum van de marker
        x_center = int(np.mean(corners[i][0][:, 0]))
        y_center = int(np.mean(corners[i][0][:, 1]))
        x_center_offset = x_center - BLACK_BAR_WIDTH
       
        # Controleer of de marker binnen de finish-zone ligt
        if cv2.pointPolygonTest(finish_box, (x_center, y_center), False) >= 0:
            if not car.finished:
                current_time = time.time()
                if current_time - car.last_lap_time > race_manager.cooldown_time:
                    car.increment_lap(current_time, TOTAL_LAPS)
        
        # Bepaal de grootte van de marker om de afstand en de schaalfactor te berekenen
        width = np.linalg.norm(corners[i][0][0] - corners[i][0][1])
        height = np.linalg.norm(corners[i][0][0] - corners[i][0][3])
        marker_size = (width + height) / 2
        distance = (MARKER_REAL_WIDTH * FOCAL_LENGTH) / marker_size
        scale_factor = max(INITIAL_SCALE_FACTOR * (1 / distance), MIN_SCALE_FACTOR)
        
        # Update de positie en schaal van de auto
        car.update_position(x_center, y_center, scale_factor)
        # overlay_image(new_frame, car.car_image, x_center, y_center, scale_factor)
            
def overlay_position_indicator(frame, car):
    """
    Overlayt een positie-indicator op de auto-afbeelding, zodat de huidige racepositie visueel wordt weergegeven.
    
    Parameters:
        frame (numpy.ndarray): Het frame waarop de indicator getekend wordt.
        car (Car): Het Car-object waarvan de positie, schaal (scale_factor) en positie (position) gebruikt worden.
    """
    if car.position is None or car.x is None or car.y is None:
        return

    # Bepaal de grootte van de indicator, afhankelijk van de schaal van de auto
    indicator_radius = int(30 * car.scale_factor)
    
    # Kies de kleur op basis van de positie:
    # Eerste plaats: goud (0, 215, 255), tweede plaats: zilver, derde plaats: brons.
    # Voor overige posities gebruiken we wit.
    if car.position == 1:
        indicator_color = (0, 215, 255)  # Goud
    elif car.position == 2:
        indicator_color = (192, 192, 192)  # Zilver
    elif car.position == 3:
        indicator_color = (205, 127, 50)   # Brons
    else:
        indicator_color = (255, 255, 255)  # Wit voor overige posities
        
    # Voeg een horizontale offset toe; positieve waarde verplaatst naar rechts, negatieve naar links.
    horizontal_offset = BLACK_BAR_WIDTH - 50 # Pas deze waarde aan naar wens.    

    # Bepaal het centrum van de indicator: positioneer deze boven de auto
    indicator_center = (
        int(car.x) + horizontal_offset,
        int(car.y -150 * car.scale_factor))

    # Teken de cirkel op het frame
    cv2.circle(frame, indicator_center, indicator_radius, indicator_color, -1)

    # Bereken de positie voor de tekst zodat deze gecentreerd in de cirkel komt
    text = str(car.position)
    font_scale = 1.0 * car.scale_factor
    (text_width, text_height), _ = cv2.getTextSize(text, FONT, font_scale, 2)
    text_x = indicator_center[0] - text_width // 2
    text_y = indicator_center[1] + text_height // 2 
    
    # **Nieuwe toevoeging:** Teken de progress-waarde naast de indicator.
    progress_text = f"P: {car.progress}"
    # Stel bijvoorbeeld een offset in voor de progress tekst (bijvoorbeeld 20 pixels naar rechts en 0 pixels verticaal)
    progress_offset_x = indicator_radius + 50  # 10 extra pixels naast de cirkel
    progress_offset_y = 50
    progress_position = (indicator_center[0] + progress_offset_x, indicator_center[1] + progress_offset_y)
    print(f"Auto {car.marker_id}: progress = {car.progress}")
    

    # Teken de positie als tekst over de cirkel
    cv2.putText(frame, text, (text_x, text_y), FONT, font_scale, (0, 0, 0), 2, LINE_TYPE)

def display_car_info(cars, frame, current_time, race_manager):
    """
    Toont informatie over elke auto op het frame. Dit omvat:
      - Ronde-informatie: de huidige lap of of de auto 'Finished' is
      - Lap Complete melding en de lap-tijd (indien recent voltooid)
      - Totale racetijd en de snelste lap
      - De overlay van de positie-indicator op de auto
    """
    for car in cars.values():
        color = car.color
        pos = car.lap_position           # Positie voor de basis tekst (bepaalde zijbalk)
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
            total_race_time = car.get_total_race_time(race_manager.race_start_time, current_time)
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

        # Verwerk het frame: dit omvat het tekenen van het parcours,
        # finish-zone, countdown, marker-detectie, en overlays
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
