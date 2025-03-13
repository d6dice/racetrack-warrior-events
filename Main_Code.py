#main.py
import cv2
import numpy as np
import time
import cv2.aruco as aruco

from config_1 import (
    FONT, FONT_SCALE_SIDEBAR, FONT_SCALE_RANKING_BAR, THICKNESS, LINE_TYPE,
    COLOR_GREEN, COLOR_BLUE, COLOR_WHITE, COLOR_RED,
    LAP_COMPLETE_DURATION, COOLDOWN_TIME,
    MARKER_REAL_WIDTH, FOCAL_LENGTH, INITIAL_SCALE_FACTOR, MIN_SCALE_FACTOR,
    RANKING_BAR_CONFIG, PATH_POINTS, PATH_WIDTH,
    FINISH_ZONE, CAMERA_INDEX, BLACK_BAR_WIDTH,
    START_TEXT, START_TEXT_POSITION, START_TEXT_FONT_SCALE, START_TEXT_COLOR, START_TEXT_THICKNESS,
    COUNTDOWN_FONT_SCALE, COUNTDOWN_COLOR, COUNTDOWN_THICKNESS, COUNTDOWN_OFFSET_X, COUNTDOWN_OFFSET_Y,
    GO_TEXT, GO_TEXT_FONT_SCALE, GO_TEXT_COLOR, GO_TEXT_THICKNESS, GO_TEXT_OFFSET_X, GO_TEXT_OFFSET_Y
)
from car_1 import Car
from race_manager_1 import RaceManager
from utils_1 import overlay_image
from image_utils_1 import load_image
from path_utils_1 import expand_path
from ranking_bar_1 import draw_ranking_bar

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
    Sorteert de auto's op basis van hun huidige lap en hun progressie binnen die lap.
    - Eerst sorteren we op lap_count (auto met meer afgeronde rondes komt eerst).
    - Binnen dezelfde lap sorteren we op progress (afgelegde afstand langs het parcours).
    Bijgewerkte posities worden opgeslagen in elk Car-object.

    Args:
        cars (dict): Dictionary met Car-objecten.

    Returns:
        list: Een gesorteerde lijst van Car-objecten.
    """
    from config import PATH_POINTS

    def calculate_progress(car):
        """Berekent hoe ver een auto gevorderd is langs het parcours."""
        if car.x is None or car.y is None:
            return 0
        car_position = np.array([car.x, car.y])
        closest_index = min(
            enumerate(PATH_POINTS),
            key=lambda item: np.linalg.norm(car_position - np.array(item[1]))
        )[0]
        return closest_index

    # Werk progress voor elke auto bij
    for car in cars.values():
        car.progress = calculate_progress(car)

    # Sorteer auto's op lap_count en progress
    sorted_cars = sorted(
        cars.values(),
        key=lambda car: (car.lap_count, car.progress),
        reverse=True
    )

    # Update de positie in elk Car-object
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
    Update de progress van elke auto (langs de centerline), update de car rankings en 
    tekent vervolgens de auto-informatie overlays en de ranking bar.
    
    Returns:
        frame: Het frame met toegevoegde overlays.
    """
    # Update progress voor elke auto (hulp via project_to_centerline)
    for car in cars.values():
        if car.x is not None and car.y is not None:
            progress = project_to_centerline((car.x, car.y), PATH_POINTS)
            car.progress = progress
            # Debug: toon de progress-waarde (optioneel)
            #cv2.putText(frame, f"P: {progress:.1f}", (car.x, car.y - 20),
             #           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    # Sorteer de auto's op basis van lap en progress en update hun positie
    sorted_cars = sort_cars_by_position(cars)
    
    # Update auto informatie (zoals ronde tijden en ranking)
    current_time = time.time()
    display_car_info(cars, frame, current_time, race_manager)
    
    # Teken de ranking bar en geef het aangepaste frame terug
    return draw_ranking_bar(frame, sorted_cars, RANKING_BAR_CONFIG)

def process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path):
    """
    Verwerkt één frame voor de race:
      - Maakt een nieuw frame met extra ruimte voor de zwarte balken en ranking bar.
      - Voert, indien de race gestart is, de marker-detectie en overlays uit.
      - Als de race nog niet gestart is, worden alleen de zwarte balken zichtbaar (zonder overliggende teksten of auto-afbeeldingen).
    
    Args:
        frame (numpy.ndarray): Het originele videobeeld.
        race_manager (RaceManager): Het object dat de status van de race beheert.
        cars (dict): Dictionary met Car-objecten.
        parameters: ArUco detectie-parameters.
        aruco_dict: Het ArUco-dictionary.
        expanded_path (numpy.ndarray): Het traject (pad) als een array met punten.
    
    Returns:
        new_frame (numpy.ndarray): Het uiteindelijke frame.
    """
    # Maak een kopie van het originele frame (zonder overlays) voor de basis
    base_frame = frame.copy()
    
    # Bepaal de nieuwe afmetingen met extra ruimte voor zijbalken en de ranking bar.
    ranking_bar_height = RANKING_BAR_CONFIG['ranking_bar_height']
    new_width = frame.shape[1] + 2 * BLACK_BAR_WIDTH
    new_height = frame.shape[0] + ranking_bar_height
    new_frame = np.zeros((new_height, new_width, 3), dtype=np.uint8)
    
    # Plaats het originele beeld in het centrale gebied van new_frame
    new_frame[0:frame.shape[0], BLACK_BAR_WIDTH:BLACK_BAR_WIDTH + frame.shape[1]] = base_frame
    
    # Pre-race fase: als de race nog niet gestart is,
    # geef dan direct new_frame (met de zwarte balken) terug zonder verdere overlays.
    if not race_manager.race_started:
        # Optioneel: Als je wel een countdown wilt tonen, kun je de handle_countdown functie op new_frame aanroepen
        handle_countdown(new_frame, race_manager, cars)    # Zorgt ervoor dat countdown in new_frame getekend wordt.
        return new_frame
    
    # Wanneer de race gestart is, werken we verder:
    
    # Voer ArUco-detectie uit op een kopie van de oorspronkelijke frame (of op base_frame)
    gray = cv2.cvtColor(base_frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    if ids is not None and len(ids) > 0:
        process_markers(cars, corners, ids, base_frame, race_manager)
    
    # Werk new_frame bij, zodat de updates in base_frame (bv. auto posities) worden meegenomen:
    new_frame[0:frame.shape[0], BLACK_BAR_WIDTH:BLACK_BAR_WIDTH + frame.shape[1]] = base_frame
    
    # Update de auto-positie-informatie t.a.v. de nieuwe frame-afmetingen
    update_car_positions(cars, new_width, new_height)
    
    # Teken het pad en de finish-zone
    draw_race_track(new_frame, expanded_path)
    draw_finish_zone(new_frame)
    
    # Voeg de overlays toe (zoals auto-informatie en ranking bar)
    new_frame = update_and_draw_overlays(new_frame, cars, race_manager)
    
    # Als de race net gestart is, toon "GO!" kort
    if race_manager.race_started and (time.time() - race_manager.race_start_time < 1):
        pos = (new_frame.shape[1] // 2 - GO_TEXT_OFFSET_X,
               new_frame.shape[0] // 2 + GO_TEXT_OFFSET_Y)
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
        overlay_image(new_frame, car.car_image, x_center, y_center, scale_factor)
            
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
