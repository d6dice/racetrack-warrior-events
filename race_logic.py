# race_logic
import cv2
import numpy as np
import time

from path_utils import compute_cumulative_distances, calculate_progress_distance
from tracking_utils import project_to_centerline
from config import *
from overlay_utils import draw_text, draw_race_track, draw_finish_zone, update_and_draw_overlays, draw_rotated_box

def sort_cars_by_position(cars):
    """
    Sorteert de auto's op basis van hun afgeronde lappen en de progress (cumulatieve afstand)
    langs het traject.
    """
    cum = compute_cumulative_distances(PATH_POINTS)
    total_distance = cum[-1]

    start_point = (350, 50)
    start_offset = project_to_centerline(start_point, PATH_POINTS)

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
    Bereken en update de overlay-posities voor ieder Car-object.
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

        new_lap_y = base_lap_y
        new_complete_y = base_complete_y

        car.lap_position = (new_lap_x, new_lap_y)
        car.lap_complete_position = (new_complete_x, new_complete_y)

def handle_countdown(frame, race_manager, cars):
    """
    Behandelt de pre-race fase.
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
    base_frame = frame.copy()
    frame_height, frame_width = base_frame.shape[:2]

    gray = cv2.cvtColor(base_frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    if ids is not None and len(ids) > 0:
        process_markers(cars, corners, ids, base_frame, race_manager)

    ranking_bar_height = RANKING_BAR_CONFIG['ranking_bar_height']
    composite_width = frame_width + 2 * BLACK_BAR_WIDTH
    composite_height = frame_height + ranking_bar_height
    new_frame = np.zeros((composite_height, composite_width, 3), dtype=np.uint8)

    cam_region = (slice(0, frame_height), slice(BLACK_BAR_WIDTH, BLACK_BAR_WIDTH + frame_width))
    new_frame[cam_region] = base_frame

    if not race_manager.race_started:
        handle_countdown(new_frame, race_manager, cars)
        return new_frame

    new_frame[cam_region] = base_frame

    draw_race_track(new_frame, expanded_path)
    draw_rotated_box(new_frame, FINISH_ZONE, color=(255, 0, 0), label="Finish Zone")
    draw_rotated_box(new_frame, CHECKPOINT_ZONE, color=(0, 255, 0), label="Checkpoint Zone")

    update_car_positions(cars, composite_width, composite_height)

    for car in cars.values():
        if car.x is not None and car.y is not None:
            car.display_x = car.x
            car.display_y = car.y
        else:
            print(f"Warning: Car {car.marker_id} heeft geen geldige positie (x={car.x}, y={car.y}); overlay overslaan.")

    new_frame = update_and_draw_overlays(new_frame, cars, race_manager)

    if cars and all(car.finished for car in cars.values()):
        final_finish_time = max(car.finish_time for car in cars.values() if car.finish_time is not None)
        if time.time() - final_finish_time >= FINAL_OVERLAY_DELAY:
            sorted_cars = sort_cars_by_position(cars)
            new_frame = draw_final_ranking_overlay(new_frame, sorted_cars)

    return new_frame

def process_markers(cars, corners, ids, new_frame, race_manager):
    """
    Verwerkt de gedetecteerde ArUco-markers.
    """
    cv2.aruco.drawDetectedMarkers(new_frame, corners, ids)

    finish_box_points = cv2.boxPoints(FINISH_ZONE)
    finish_box_points = np.int32(finish_box_points)

    checkpoint_box_points = cv2.boxPoints(CHECKPOINT_ZONE)
    checkpoint_box_points = np.int32(checkpoint_box_points)

    for i, marker_id in enumerate(ids.flatten()):
        if marker_id not in cars:
            continue

        car = cars[marker_id]

        x_center = int(np.mean(corners[i][0][:, 0]))
        y_center = int(np.mean(corners[i][0][:, 1]))

        if cv2.pointPolygonTest(checkpoint_box_points, (x_center, y_center), False) >= 0:
            car.passed_checkpoint = True
            print(f"Marker ID {marker_id}: Auto heeft het checkpoint bereikt.")

        if cv2.pointPolygonTest(finish_box_points, (x_center, y_center), False) >= 0:
            if car.passed_checkpoint:
                current_time = time.time()
                if current_time - car.last_lap_time > race_manager.cooldown_time:
                    car.increment_lap(current_time, TOTAL_LAPS, race_manager)
                    car.passed_checkpoint = False
                else:
                    print(f"Marker ID {marker_id} is in cooldown en kan de lap niet verhogen.")
            else:
                print(f"Marker ID {marker_id}: Auto heeft het checkpoint niet bereikt. Lap wordt niet verhoogd.")

        width = np.linalg.norm(corners[i][0][0] - corners[i][0][1])
        height = np.linalg.norm(corners[i][0][0] - corners[i][0][3])
        marker_size = (width + height) / 2
        distance = (MARKER_REAL_WIDTH * FOCAL_LENGTH) / marker_size
        scale_factor = max(INITIAL_SCALE_FACTOR * (1 / distance), MIN_SCALE_FACTOR)

        car.update_position(x_center, y_center, scale_factor)