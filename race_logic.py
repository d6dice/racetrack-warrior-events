#race_logic
import cv2
import numpy as np
import time

from path_utils import compute_cumulative_distances, calculate_progress_distance, expand_path
from tracking_utils import project_to_centerline
from config import *
from overlay_utils import draw_text, draw_race_track, draw_finish_zone, draw_checkpoint_zone, update_and_draw_overlays, draw_final_ranking_overlay, display_car_info
from race_manager import RaceManager

def sort_cars_by_position(cars):
    """
    Sorteert de auto's op basis van hun afgeronde lappen en de progress (cumulatieve afstand)
    langs het traject. Hierbij wordt eerst een start_offset berekend aan de hand van een bekend 
    startpunt (350,50). Vervolgens wordt voor elke auto de raw progress bepaald en aangepast 
    met die offset. Daarna worden de auto's opgesplitst in gefinished en niet‒finished auto's:

      - Gefinished auto's (waarbij car.finished True is en car.final_position is ingesteld) 
        worden gesorteerd op final_position zodat het eindklassement vaststaat.
      - Niet‒finished auto's worden gesorteerd op lap_count en progress (in afnemende volgorde).
    
    Tenslotte krijgen alle auto's een overall positie (position) toe op basis van de gesorteerde volgorde.
    """
    # Bereken de cumulatieve afstanden langs het traject
    cum = compute_cumulative_distances(PATH_POINTS)
    total_distance = cum[-1]
    
    # Bereken de start_offset op basis van een bekend startpunt gedefinieerd in PATH_POINTS
    start_point = (350, 50)
    print(f"Startpunt voor offsetberekening: {start_point}")
    start_offset = project_to_centerline(start_point, PATH_POINTS)
    print(f"Start_offset: {start_offset}")
    
    # Voor elke auto, als positie bekend is, bereken raw progress en pas de offset toe
    for car in cars.values():
        if car.x is not None and car.y is not None:
            raw_progress = calculate_progress_distance(car, PATH_POINTS)
            car.progress = (raw_progress - start_offset) % total_distance
        else:
            car.progress = 0

    # Splits auto's op in gefinished en niet-finished
    finished_cars = [car for car in cars.values() if car.finished and car.final_position is not None]
    non_finished_cars = [car for car in cars.values() if not (car.finished and car.final_position is not None)]
    
    # Sorteer de gefinished auto's op hun final_position (laagste eerst, want 1 is eerste finish)
    finished_cars.sort(key=lambda car: car.final_position)
    
    # Sorteer de niet-finished auto's zoals voorheen, op lap_count en progress (in afnemende volgorde)
    non_finished_cars.sort(key=lambda car: (car.lap_count, car.progress), reverse=True)
    
    # Combineer beide lijsten: de gefinished auto's komen eerst
    sorted_cars = finished_cars + non_finished_cars
    
    # Ken voor alle auto's de overall positie (1-based ranking) toe op basis van de gesorteerde volgorde
    for idx, car in enumerate(sorted_cars):
        car.position = idx + 1

    # Debug: Print de gesorteerde lijst met relevante attributen
    print("Gesorteerde auto's (position, marker_id, finished, final_position, lap_count, progress):")
    for car in sorted_cars:
        print(f"Pos {car.position}: Marker ID {car.marker_id}, Finished: {car.finished}, Final Pos: {car.final_position}, Lap Count: {car.lap_count}, Progress: {car.progress:.2f}")

    return sorted_cars

def update_car_positions(cars, frame_width, frame_height):
    """
    Bereken en update de overlay-posities voor ieder Car-object op basis van het frame.
    
    Deze versie maakt geen onderscheid tussen auto's; voor elke auto wordt dezelfde 
    transformatie toegepast. De basis-offsets worden éénmalig vastgelegd (zoals geconfigureerd
    in CAR_CONFIG). Vervolgens wordt er een globale offset (bijvoorbeeld BLACK_BAR_WIDTH) opgeteld.
    
    Zo bepaal je volledig via de config de uiteindelijke positie van de overlay.
    
    Args:
        cars (dict): Dictionary met Car-objecten (key: marker_id).
        frame_width (int): Breedte van het camerafeel.
        frame_height (int): Hoogte van het camerafeel.
    """
    for car in cars.values():
        # Zorg dat de originele overlay-posities éénmalig worden opgeslagen als basiswaarden.
        if not hasattr(car, "base_lap_position"):
            car.base_lap_position = car.lap_position  # (bijv. (-40, 100) of andere waarde zoals je dat wilt)
        if not hasattr(car, "base_lap_complete_position"):
            car.base_lap_complete_position = car.lap_complete_position
    
        # Haal de basiswaarden op.
        base_lap_x, base_lap_y = car.base_lap_position
        base_complete_x, base_complete_y = car.base_lap_complete_position
    
        # Pas een uniforme transformatie toe: voeg een vaste offset toe.
        # Als je wilt dat de uiteindelijke positie in de linker sidebar komt, regel je dit door in de config
        # de juiste basiswaarde mee te geven (bijv. een negatief getal) en hier een vaste offset op te tellen.
        new_lap_x = base_lap_x + BLACK_BAR_WIDTH
        new_complete_x = base_complete_x + BLACK_BAR_WIDTH
    
        # De y-waarden blijven onveranderd
        new_lap_y = base_lap_y
        new_complete_y = base_complete_y
    
        # Update de overlay-posities van de auto
        car.lap_position = (new_lap_x, new_lap_y)
        car.lap_complete_position = (new_complete_x, new_complete_y)
        
        # Debug: Print de berekende overlay-posities voor controle
        print(f"Car {car.color_key}: overlay lap_position: ({new_lap_x}, {new_lap_y}), "
              f"lap_complete_position: ({new_complete_x}, {new_complete_y})")

def initialize_frame(frame, cars, race_manager):
    """
    Initialiseert het volledige frame met alle vaste overlays, zoals:
    - Zwarte balken
    - Ranking bar
    - Baan, finishzone en controlezone
    - Auto-posities
    """
    # Bereken compositie-afmetingen
    ranking_bar_height = RANKING_BAR_CONFIG['ranking_bar_height']
    composite_width = frame.shape[1] + 2 * BLACK_BAR_WIDTH
    composite_height = frame.shape[0] + ranking_bar_height

    # Maak een nieuw frame voor de volledige compositie
    new_frame = np.zeros((composite_height, composite_width, 3), dtype=np.uint8)
    cam_region = (slice(0, frame.shape[0]), slice(BLACK_BAR_WIDTH, BLACK_BAR_WIDTH + frame.shape[1]))
    new_frame[cam_region] = frame

    # Debug: Controleer de afmetingen en regio's
    print(f"Composite frame: width = {composite_width}, height = {composite_height}")
    print(f"Camera regio: {cam_region}")

    # Teken vaste overlays
    draw_race_track(new_frame, expand_path(PATH_POINTS, PATH_WIDTH))
    draw_finish_zone(new_frame)
    draw_checkpoint_zone(new_frame)

    # Teken auto-informatie direct bij het opstarten
    current_time = time.time()
    for car_id, car in cars.items():
        # Pas de BLACK_BAR_WIDTH toe op de X-coördinaten van de auto
        adjusted_x = car.x + BLACK_BAR_WIDTH if car.x else None
        car.x = adjusted_x  # Update de auto-coördinaten met de offset
        print(f"Auto {car_id} aangepaste x-coördinaat: {adjusted_x}")

        display_car_info({car_id: car}, new_frame, current_time, race_manager)

    return new_frame

def process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path):
    """
    Verwerkt een frame voor de race en bouwt een definitieve composiet op:
    - Detecteert ArUco-markers en verwerkt deze.
    - Achtergrondlaag: het originele camerabeeld wordt gespiegeld.
    - Overlaylaag: alle overlays (traject, finish-zone, auto-informatie, indicatoren, "GO!"-tekst).
    """
    # Maak een copy van het originele frame
    base_frame = frame.copy()
    frame_height, frame_width = base_frame.shape[:2]
    
    # Initialiseer alles als het de eerste frame is
    if not race_manager.initialized:
        initialized_frame = initialize_frame(base_frame, cars, race_manager)
        race_manager.initialized = True
        return initialized_frame
    
    # ArUco-detectie op het originele, ongespiegelde beeld
    print("DEBUG: Start ArUco-detectie in process_frame.")
    gray = cv2.cvtColor(base_frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    if ids is not None and len(ids) > 0:
        print(f"DEBUG: Gedetecteerde ArUco-ID's: {ids.flatten()}")
        process_markers(cars, corners, ids, base_frame, race_manager)
    else:
        print("⚠️ DEBUG: Geen ArUco-markers gedetecteerd.")

    # Maak de compositie: extra ruimte voor de zwarte balken en ranking bar
    ranking_bar_height = RANKING_BAR_CONFIG['ranking_bar_height']
    composite_width = frame_width + 2 * BLACK_BAR_WIDTH
    composite_height = frame_height + ranking_bar_height
    new_frame = np.zeros((composite_height, composite_width, 3), dtype=np.uint8)
    
    # Definieer de cameraregion in het nieuwe canvas
    cam_region = (slice(0, frame_height), slice(BLACK_BAR_WIDTH, BLACK_BAR_WIDTH + frame_width))
    new_frame[cam_region] = base_frame  # Plaats het originele beeld eerst

    # Initialiseer alles als het de eerste frame is
    if not race_manager.initialized:
        initialized_frame = initialize_frame(base_frame, cars, race_manager)
        race_manager.initialized = True
        return initialized_frame

    # Teken countdown of "GO!" als de race nog niet is gestart
    if not race_manager.race_started:
        handle_countdown(new_frame, race_manager, cars)
        return new_frame

    # Teken de vaste overlays
    draw_race_track(new_frame, expand_path(PATH_POINTS, PATH_WIDTH))
    draw_finish_zone(new_frame)
    draw_checkpoint_zone(new_frame)

    # Update auto-posities relatief aan de composiet
    update_car_positions(cars, composite_width, composite_height)
    
    # Teken auto-informatie
    current_time = time.time()  # Huidige tijd
    display_car_info(cars, new_frame, current_time, race_manager)    

    # Bereken voor iedere auto de display-coördinaten
    for car in cars.values():
        if car.x is not None and car.y is not None:
            car.display_x = car.x
            car.display_y = car.y
        else:
            print(f"⚠️ Warning: Car {car.marker_id} heeft geen geldige positie (x={car.x}, y={car.y}); overlay overslaan.")
    
    # Teken als laatste alle overlays, inclusief de auto-afbeeldingen en indicatoren
    new_frame = update_and_draw_overlays(new_frame, cars, race_manager)

    # Indien de race net gestart is, teken "GO!" in de cameraregion
    if race_manager.race_started and (time.time() - race_manager.race_start_time < 1):
        pos = (BLACK_BAR_WIDTH + frame_width // 2 - GO_TEXT_OFFSET_X,
               frame_height // 2 + GO_TEXT_OFFSET_Y)
        draw_text(new_frame, GO_TEXT, pos, GO_TEXT_COLOR, GO_TEXT_FONT_SCALE, GO_TEXT_THICKNESS)

    # Controleer of alle auto's gefinished zijn
    if cars and all(car.finished for car in cars.values()):
        final_finish_time = max(car.finish_time for car in cars.values() if car.finish_time is not None)
        if time.time() - final_finish_time >= FINAL_OVERLAY_DELAY:
            sorted_cars = sort_cars_by_position(cars)
            new_frame = draw_final_ranking_overlay(new_frame, sorted_cars)
        else:
            print(f"DEBUG: Final overlay delay nog aan de gang, nog {FINAL_OVERLAY_DELAY - (time.time() - final_finish_time):.1f} sec te gaan.")
        
    return new_frame

def handle_countdown(frame, race_manager, cars):
    """
    Behandelt de pre-race fase:
    - Toont "Ready?" en start pas daarna de countdown.
    - Als de countdown bezig is, wordt het nummer getoond; bij 0 start de race en verschijnt 'GO!'.
    """
    # Controleer of we nog in de "Ready?"-fase zitten
    if not hasattr(race_manager, "ready_shown"):
        # Teken "Ready?" op het frame
        draw_text(frame, START_TEXT, START_TEXT_POSITION,
                  START_TEXT_COLOR, START_TEXT_FONT_SCALE, START_TEXT_THICKNESS)
        
        # Toon het frame met "Ready?" in het venster
        cv2.imshow("Race Track Warrior", frame)
        cv2.waitKey(1000)  # Wacht 1 seconde om "Ready?" weer te geven
        
        # Markeer dat "Ready?" is getoond en start de countdown-timer
        race_manager.ready_shown = True
        race_manager.countdown_start_time = time.time()
        return True  # Geef aan dat we in de "Ready?"-fase zitten
    else:
        # Countdown begint pas nu
        countdown_number = race_manager.update_countdown()
        if countdown_number is not None:
            if countdown_number > 0:
                # Teken het countdown-nummer op het frame
                pos = (frame.shape[1] // 2 - COUNTDOWN_OFFSET_X,
                       frame.shape[0] // 2 + COUNTDOWN_OFFSET_Y)
                draw_text(frame, str(countdown_number), pos,
                          COUNTDOWN_COLOR, COUNTDOWN_FONT_SCALE, COUNTDOWN_THICKNESS)
            else:
                # Teken "GO!" op het frame
                pos = (frame.shape[1] // 2 - GO_TEXT_OFFSET_X,
                       frame.shape[0] // 2 + GO_TEXT_OFFSET_Y)
                draw_text(frame, GO_TEXT, pos,
                          GO_TEXT_COLOR, GO_TEXT_FONT_SCALE, GO_TEXT_THICKNESS)
                if not race_manager.race_started:
                    race_manager.start_race()
                    for car in cars.values():
                        car.last_lap_time = race_manager.race_start_time
            return True  # Geef aan dat we nog in de countdown/race-start zitten
    return False  # Countdown is voltooid, ga verder met de race

def process_markers(cars, corners, ids, new_frame, race_manager):
    """
    Verwerkt de gedetecteerde ArUco-markers:
      - Controleert dubbele verwerking binnen dezelfde detectieronde.
      - Bereken het centrum (x, y) van elke marker.
      - Update de positie van de auto (inclusief de opslag van de vorige positie).
    """
    # Set om al verwerkte markers in deze detectieronde bij te houden
    processed_markers = set()

    # Teken alle gedetecteerde markers in het frame
    cv2.aruco.drawDetectedMarkers(new_frame, corners, ids)
    print(f"Detected IDs: {ids}")
    print(f"Detected Corners: {corners}")
    
    # Bereken de finish- en checkpoint-zones als polygonen
    finish_box = cv2.boxPoints(FINISH_ZONE)
    finish_box = np.int32(finish_box)
    finish_box[:, 0] -= BLACK_BAR_WIDTH  # Correctie voor zijbalk
    
    checkpoint_box = cv2.boxPoints(CHECKPOINT_ZONE)
    checkpoint_box = np.int32(checkpoint_box)
    checkpoint_box[:, 0] -= BLACK_BAR_WIDTH  # Correctie voor zijbalk
    
    for i, marker_id in enumerate(ids.flatten()):
        # Controleer of de marker al verwerkt is in deze detectieronde
        if marker_id in processed_markers:
            print(f"Marker ID {marker_id} is al verwerkt in deze detectieronde.")
            continue
        processed_markers.add(marker_id)

        # Controleer of deze marker overeenkomt met een auto
        if marker_id not in cars:
            print(f"Marker ID {marker_id} komt niet overeen met een auto.")
            continue
    
        car = cars[marker_id]
        
        # Bereken het centrum van de marker
        x_center = int(np.mean(corners[i][0][:, 0]))
        y_center = int(np.mean(corners[i][0][:, 1]))
        
        # Pas een positiecorrectie toe (indien nodig)
        x_offset = 350 - 150  # Voorbeeld: 200 pixels correctie
        y_offset = 50 - 50    # Geen verticale correctie in dit voorbeeld
        adjusted_x = x_center + x_offset
        adjusted_y = y_center + y_offset
        print(f"Marker ID {marker_id}: Aangepaste positie: x = {adjusted_x}, y = {adjusted_y}")
        
        # Controleer of de marker binnen de checkpoint-zone ligt
        if cv2.pointPolygonTest(checkpoint_box, (x_center, y_center), False) >= 0:
            car.passed_checkpoint = True
            print(f"Auto {marker_id} heeft de checkpoint gepasseerd.")
        
        # Controleer of de marker binnen de finish-zone ligt
        if cv2.pointPolygonTest(finish_box, (x_center, y_center), False) >= 0:
            # Controleer of de auto de checkpoint heeft gepasseerd en van links naar rechts beweegt
            if car.passed_checkpoint and ((car.prev_x is None) or (adjusted_x > car.prev_x)):
                if not car.finished:
                    print(f"Marker ID {marker_id} passeert de finish.")
                    car.increment_lap(time.time(), TOTAL_LAPS, race_manager)
                    # Reset de checkpoint-status na het voltooien van een lap
                    car.passed_checkpoint = False
                    # Reset de lap text timer voor de "Lap Complete" melding
                    car.lap_text_start_time = time.time()
            else:
                print(f"Marker ID {marker_id}: Auto beweegt niet in de juiste richting of heeft de checkpoint niet gepasseerd.")
        
        # Bepaal de grootte (marker_size) van de marker om de afstand en schaalfactor te berekenen
        width = np.linalg.norm(corners[i][0][0] - corners[i][0][1])
        height = np.linalg.norm(corners[i][0][0] - corners[i][0][3])
        marker_size = (width + height) / 2
        distance = (MARKER_REAL_WIDTH * FOCAL_LENGTH) / marker_size
        scale_factor = max(INITIAL_SCALE_FACTOR * (1 / distance), MIN_SCALE_FACTOR)
        print(f"Marker ID {marker_id}: width = {width}, height = {height}, marker_size = {marker_size}, distance = {distance}, scale_factor = {scale_factor}")
        
        # Update de positie van de auto
        car.update_position(adjusted_x, adjusted_y, scale_factor)
        print(f"Auto {marker_id} bijgewerkte positie: x = {car.x}, y = {car.y}, scale_factor = {car.scale_factor}")
    
    return new_frame

def process_frame_loop(cars, race_manager, cap, parameters, aruco_dict, expanded_path):
    """
    Beheert een continue lus om frames te verwerken met behulp van process_frame.
    """
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("⚠️ Geen frame ontvangen van de camera. Controleer de verbinding.")
            continue

        try:
            # Verwerk het frame via de bestaande process_frame-functie
            processed_frame = process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path)
        except Exception as e:
            print(f"❌ Fout bij verwerken frame: {e}")
            continue

        # Toon het verwerkte frame
        cv2.imshow("ArUco Auto Tracken met Ronde Detectie", processed_frame)

        # Controleer of het venster gesloten is of op Esc is gedrukt
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or cv2.getWindowProperty("ArUco Auto Tracken met Ronde Detectie", cv2.WND_PROP_VISIBLE) < 1:
            break

    # Zorg ervoor dat de camera netjes wordt vrijgegeven en vensters worden gesloten
    cap.release()
    cv2.destroyAllWindows()
    
def run_race(cars, race_manager, cap, stop_event, shared_frame, frame_lock):
    """
    Coördineert de race door camera-frames te verwerken en de gedeelde framebuffer bij te werken.

    Parameters:
    - cars: Dictionary met auto-objecten.
    - race_manager: Het RaceManager-object dat de race beheert.
    - cap: OpenCV VideoCapture-object voor toegang tot de camera.
    - stop_event: threading.Event-object om de race netjes te stoppen.
    - shared_frame: Gedeelde lijst voor het bijhouden van het huidige frame.
    - frame_lock: threading.Lock-object voor thread-safe toegang tot shared_frame.
    """
    try:
        print("run_race is gestart!")  # Debug-uitvoer

        # Definieer het ArUco-dictionary en de detectieparameters
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()

        # Maak het uitgezette pad (expanded_path) voor het parcours
        expanded_path = expand_path(PATH_POINTS, width=PATH_WIDTH)
        print("Expanded path succesvol gegenereerd!")  # Debug-uitvoer

        # Start de race-loop
        race_manager.initialized = False  # Nieuw attribuut om te controleren of alles is voorbereid
        while not stop_event.is_set():  # Controleer het stop_event
            # Lees een frame van de camera
            ret, frame = cap.read()
            if not ret or frame is None:
                print("⚠️ Geen frame ontvangen van de camera. Controleer de verbinding.")
                continue

            print("✅ Frame ontvangen!")  # Debug-uitvoer

            # Probeer het frame te verwerken
            try:
                processed_frame = process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path)
            except Exception as e:
                print(f"❌ Fout bij verwerken frame: {e}")
                continue

            # Update de gedeelde framebuffer met het verwerkte frame
            with frame_lock:
                shared_frame[0] = processed_frame

        # Zorg ervoor dat de camera netjes wordt vrijgegeven
        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"❌ Onverwachte fout in run_race: {e}")
        cap.release()
        cv2.destroyAllWindows()