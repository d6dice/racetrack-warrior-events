# Main.py

import cv2
import numpy as np
import time
import cv2.aruco as aruco

from config import *
from car import Car
from race_manager import RaceManager
from image_utils import load_image, overlay_image
from path_utils import expand_path, compute_cumulative_distances, calculate_progress_distance, expand_path
from ranking_bar import draw_ranking_bar
from tracking_utils import project_to_centerline, process_detected_markers
from race_logic import sort_cars_by_position, update_car_positions, handle_countdown, process_frame
from overlay_utils import draw_final_ranking_overlay, overlay_position_indicator, draw_race_track, draw_finish_zone, draw_text, update_and_draw_overlays, display_car_info
from car_utils import initialize_cars
import signal

def handle_close(sig, frame):
    print("Programma wordt afgesloten...")
    cv2.destroyAllWindows()
    exit(0)

signal.signal(signal.SIGINT, handle_close)
signal.signal(signal.SIGTERM, handle_close)

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

        # Controleer of het venster is gesloten
        if cv2.getWindowProperty("ArUco Auto Tracken met Ronde Detectie", cv2.WND_PROP_VISIBLE) < 1:
            break

    # Zorg ervoor dat de camera netjes wordt vrijgegeven en vensters worden gesloten.
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()