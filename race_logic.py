# race_logic.py

import cv2
import numpy as np
import time
from path_utils import compute_cumulative_distances, calculate_progress_distance, expand_path
from tracking_utils import project_to_centerline
from overlay_utils import (
    draw_text,
    draw_race_track,
    draw_finish_zone,
    draw_checkpoint_zone,
    update_and_draw_overlays,
    draw_final_ranking_overlay,
)
from ranking_bar import draw_ranking_bar
from config import *

def sort_cars_by_position(cars):
    """
    Sorteert de auto's op basis van hun afgeronde lappen en de progress langs het traject.
    """
    cum = compute_cumulative_distances(PATH_POINTS)
    total_distance = cum[-1]
    start_offset = project_to_centerline((350, 50), PATH_POINTS)

    for car in cars.values():
        if car.x is not None and car.y is not None:
            raw_progress = calculate_progress_distance(car, PATH_POINTS)
            car.progress = (raw_progress - start_offset) % total_distance
        else:
            car.progress = 0

    finished_cars = [car for car in cars.values() if car.finished and car.final_position is not None]
    non_finished_cars = [car for car in cars.values() if not (car.finished and car.final_position is not None)]

    finished_cars.sort(key=lambda car: car.final_position)
    non_finished_cars.sort(key=lambda car: (car.lap_count, car.progress), reverse=True)

    sorted_cars = finished_cars + non_finished_cars

    for idx, car in enumerate(sorted_cars):
        car.position = idx + 1

    return sorted_cars

def update_car_positions(cars, frame_width, frame_height):
    """
    Bereken en update de overlay-posities voor ieder Car-object op basis van het frame.
    """
    for car in cars.values():
        if not hasattr(car, "base_lap_position"):
            car.base_lap_position = car.lap_position
        if not hasattr(car, "base_lap_complete_position"):
            car.base_lap_complete_position = car.lap_complete_position

        base_lap_x, base_lap_y = car.base_lap_position
        base_complete_x, base_complete_y = car.base_lap_complete_position

        new_lap_x = base_lap_x + BLACK_BAR_WIDTH
        new_complete_x = base_complete_x + BLACK_BAR_WIDTH

        car.lap_position = (new_lap_x, base_lap_y)
        car.lap_complete_position = (new_complete_x, base_complete_y)

def process_markers(cars, corners, ids, new_frame, race_manager):
    """
    Verwerkt de gedetecteerde ArUco-markers:
      - Teken de markers in het frame.
      - Bereken het centrum (x, y) van elke marker.
      - Controleer of een marker binnen de finish-zone ligt en verhoog,
        indien de auto van links naar rechts beweegt, de lap.
      - Controleer of een marker door de checkpoint-zone is gegaan.
      - Bereken op basis van de marker-grootte de afstand en schaalfactor.
      - Update de positie van de auto (inclusief de opslag van de vorige positie).
    """
    cv2.aruco.drawDetectedMarkers(new_frame, corners, ids)
    print(f"Detected IDs: {ids}")
    print(f"Detected Corners: {corners}")

    finish_box = cv2.boxPoints(FINISH_ZONE)
    finish_box = np.int32(finish_box)
    finish_box[:, 0] -= BLACK_BAR_WIDTH
    print(f"Finish box (na BLACK_BAR_WIDTH-correctie): {finish_box}")

    checkpoint_box = cv2.boxPoints(CHECKPOINT_ZONE)
    checkpoint_box = np.int32(checkpoint_box)
    checkpoint_box[:, 0] -= BLACK_BAR_WIDTH

    for i, marker_id in enumerate(ids.flatten()):
        if marker_id not in cars:
            print(f"Marker ID {marker_id} komt niet overeen met een auto.")
            continue

        car = cars[marker_id]

        x_center = int(np.mean(corners[i][0][:, 0]))
        y_center = int(np.mean(corners[i][0][:, 1]))

        x_offset = 350 - 150
        y_offset = 50 - 50
        adjusted_x = x_center + x_offset
        adjusted_y = y_center + y_offset
        print(f"Marker ID {marker_id}: Aangepaste positie: x = {adjusted_x}, y = {adjusted_y}")

        if cv2.pointPolygonTest(checkpoint_box, (x_center, y_center), False) >= 0:
            car.passed_checkpoint = True
            print(f"Auto {marker_id} heeft de checkpoint gepasseerd.")

        if cv2.pointPolygonTest(finish_box, (x_center, y_center), False) >= 0:
            if car.passed_checkpoint and ((car.prev_x is None) or (adjusted_x > car.prev_x)):
                if not car.finished:
                    current_time = time.time()
                    if current_time - car.last_lap_time > race_manager.cooldown_time:
                        print(f"Marker ID {marker_id} passeert de finish.")
                        car.increment_lap(current_time, TOTAL_LAPS, race_manager)
                        car.passed_checkpoint = False
                        car.lap_text_start_time = current_time
                    else:
                        print(f"Marker ID {marker_id} is in cooldown en kan de lap niet verhogen.")
            else:
                print(f"Marker ID {marker_id}: Auto heeft de checkpoint niet gepasseerd. Geen lapverhoging.")

        width = np.linalg.norm(corners[i][0][0] - corners[i][0][1])
        height = np.linalg.norm(corners[i][0][0] - corners[i][0][3])
        marker_size = (width + height) / 2
        distance = (MARKER_REAL_WIDTH * FOCAL_LENGTH) / marker_size
        scale_factor = max(INITIAL_SCALE_FACTOR * (1 / distance), MIN_SCALE_FACTOR)
        print(f"Marker ID {marker_id}: width = {width}, height = {height}, marker_size = {marker_size}, distance = {distance}, scale_factor = {scale_factor}")

        car.update_position(adjusted_x, adjusted_y, scale_factor)
        print(f"Auto {marker_id} bijgewerkte positie: x = {car.x}, y = {car.y}, scale_factor = {car.scale_factor}")

def handle_countdown(frame, race_manager, cars):
    """
    Behandelt de countdown vóór de race.
    """
    if race_manager.countdown_start_time is None:
        draw_text(frame, START_TEXT, START_TEXT_POSITION, START_TEXT_COLOR, START_TEXT_FONT_SCALE, START_TEXT_THICKNESS)
        return True
    else:
        countdown_number = race_manager.update_countdown()
        if countdown_number is not None:
            if countdown_number > 0:
                pos = (frame.shape[1] // 2 - COUNTDOWN_OFFSET_X, frame.shape[0] // 2 + COUNTDOWN_OFFSET_Y)
                draw_text(frame, str(countdown_number), pos, COUNTDOWN_COLOR, COUNTDOWN_FONT_SCALE, COUNTDOWN_THICKNESS)
            else:
                pos = (frame.shape[1] // 2 - GO_TEXT_OFFSET_X, frame.shape[0] // 2 + GO_TEXT_OFFSET_Y)
                draw_text(frame, GO_TEXT, pos, GO_TEXT_COLOR, GO_TEXT_FONT_SCALE, GO_TEXT_THICKNESS)
                if not race_manager.race_started:
                    race_manager.start_race()
                    for car in cars.values():
                        car.last_lap_time = race_manager.race_start_time
            return True
    return False

def process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path):
    """
    Verwerkt een frame voor de race.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    if ids is not None:
        process_markers(cars, corners, ids, frame, race_manager)

    draw_race_track(frame, expanded_path)
    draw_finish_zone(frame)
    draw_checkpoint_zone(frame)
    update_and_draw_overlays(frame, cars)
    return frame

def run_race(cap, cars, race_manager):
    """
    Verwerkt frames van de camera en voert de race-logica uit.
    """
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()
    expanded_path = expand_path(PATH_POINTS, width=PATH_WIDTH)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        if handle_countdown(frame, race_manager, cars):
            cv2.imshow("ArUco Auto Tracken met Ronde Detectie", frame)
            continue

        frame = process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path)

        cv2.imshow("ArUco Auto Tracken met Ronde Detectie", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in [ord('q'), 27]:
            break
        elif key == ord('r'):
            race_manager.reset_race()
            for car in cars.values():
                car.reset()

        if cv2.getWindowProperty("ArUco Auto Tracken met Ronde Detectie", cv2.WND_PROP_VISIBLE) < 1:
            break