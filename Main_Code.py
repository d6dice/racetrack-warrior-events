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
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)

def main():
    # Controleer OpenCV-versie
    print(f"OpenCV-versie: {cv2.__version__}")

    # Open de camera
    cap = cv2.VideoCapture(CAMERA_INDEX)

    # Laad de auto-afbeeldingen
    green_car_image = load_image('D:\\werk\\warrior events\\groene_auto.png', 640, 480)
    blue_car_image = load_image('D:\\werk\\warrior events\\blauwe_auto.png', 640, 480)

    # Initialiseer auto's
    cars = {
        0: Car(marker_id=0, color=COLOR_BLUE, car_image=blue_car_image, lap_position=None, lap_complete_position=None),
        1: Car(marker_id=1, color=COLOR_GREEN, car_image=green_car_image, lap_position=None, lap_complete_position=None)
    }

    # Initialiseer de RaceManager
    race_manager = RaceManager()

    # Definieer het ArUco-dictionary en de parameters voor detectie
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()

    # Maak het pad voor de baan (ovale vorm)
    expanded_path = expand_path(PATH_POINTS, width=PATH_WIDTH)

    # Start de hoofdloop
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Frame error, probeer opnieuw...")
            continue

        # Vergroot de breedte van het frame door zwarte randen toe te voegen
        ranking_bar_height = RANKING_BAR_CONFIG['ranking_bar_height']
        new_width = frame.shape[1] + 2 * BLACK_BAR_WIDTH
        new_height = frame.shape[0] + ranking_bar_height

        # Maak een nieuw frame met een zwarte achtergrond
        new_frame = np.zeros((new_height, new_width, 3), dtype=np.uint8)
        new_frame[0:frame.shape[0], BLACK_BAR_WIDTH:BLACK_BAR_WIDTH + frame.shape[1]] = frame

        # Verkrijg de afmetingen van new_frame
        frame_width = new_frame.shape[1]
        frame_height = new_frame.shape[0]

        # Bereken de posities dynamisch voor de auto-informatie
        # Blauwe auto (rechterkant)
        x_blauw_lap = frame_width - BLACK_BAR_WIDTH + 20
        y_blauw_lap = 100
        x_blauw_complete = x_blauw_lap
        y_blauw_complete = y_blauw_lap + 50

        # Groene auto (linkerkant)
        x_groen_lap = 20
        y_groen_lap = 100
        x_groen_complete = x_groen_lap
        y_groen_complete = y_groen_lap + 50

        # Werk auto-instanties bij met de nieuwe posities
        cars[0].lap_position = (x_blauw_lap, y_blauw_lap)
        cars[0].lap_complete_position = (x_blauw_complete, y_blauw_complete)
        cars[1].lap_position = (x_groen_lap, y_groen_lap)
        cars[1].lap_complete_position = (x_groen_complete, y_groen_complete)

        # Converteer het frame naar grijswaarden
        gray = cv2.cvtColor(new_frame, cv2.COLOR_BGR2GRAY)

        # Detecteer ArUco-markers in het frame
        corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        # Teken de baan
        for points in expanded_path:
            cv2.fillPoly(new_frame, [np.array(points)], COLOR_RED)  # Teken het pad in rood

        # *** Wacht op race start ***
        if not race_manager.race_started and race_manager.countdown_start_time is None:
            cv2.putText(new_frame, START_TEXT, START_TEXT_POSITION,
                        FONT, START_TEXT_FONT_SCALE, START_TEXT_COLOR, START_TEXT_THICKNESS, LINE_TYPE)
            cv2.imshow("ArUco Auto Tracken met Ronde Detectie", new_frame)
            key = cv2.waitKey(1) & 0xFF
            if key != 255:
                print(f"Key pressed: {key}")
                if key in [13, 10]:
                    print("Start countdown initiated.")
                    race_manager.start_countdown()
                elif key == ord('q') or key == 27:
                    break
            continue

        # *** Aftelling voordat de race begint ***
        countdown_number = race_manager.update_countdown()
        if countdown_number is not None:
            print(f"Countdown number: {countdown_number}")
            if countdown_number > 0:
                countdown_position = (new_frame.shape[1] // 2 - COUNTDOWN_OFFSET_X,
                                      new_frame.shape[0] // 2 + COUNTDOWN_OFFSET_Y)
                cv2.putText(new_frame, str(countdown_number), countdown_position,
                            FONT, COUNTDOWN_FONT_SCALE, COUNTDOWN_COLOR, COUNTDOWN_THICKNESS, LINE_TYPE)
            else:
                go_position = (new_frame.shape[1] // 2 - GO_TEXT_OFFSET_X,
                               new_frame.shape[0] // 2 + GO_TEXT_OFFSET_Y)
                cv2.putText(new_frame, GO_TEXT, go_position,
                            FONT, GO_TEXT_FONT_SCALE, GO_TEXT_COLOR, GO_TEXT_THICKNESS, LINE_TYPE)
                print("GO!")
                if not race_manager.race_started:
                    race_manager.start_race()
                for car in cars.values():
                    car.last_lap_time = race_manager.race_start_time
            cv2.imshow("ArUco Auto Tracken met Ronde Detectie", new_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            continue

        # Verwerk de gedetecteerde ArUco-markers
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(new_frame, corners, ids)
            for i, marker_id in enumerate(ids.flatten()):
                if marker_id in cars:
                    car = cars[marker_id]
                    x_center = int(np.mean(corners[i][0][:, 0]))
                    y_center = int(np.mean(corners[i][0][:, 1]))
                    width = np.linalg.norm(corners[i][0][0] - corners[i][0][1])
                    height = np.linalg.norm(corners[i][0][0] - corners[i][0][3])
                    marker_size = (width + height) / 2
                    distance = (MARKER_REAL_WIDTH * FOCAL_LENGTH) / marker_size
                    scale_factor = max(INITIAL_SCALE_FACTOR * (1 / distance), MIN_SCALE_FACTOR)
                    car.update_position(x_center, y_center, scale_factor)
                    overlay_image(new_frame, car.car_image, x_center, y_center, scale_factor)
                    # Alleen finish-check uitvoeren als de auto nog niet gefinished is
                    if (FINISH_ZONE[0][0] <= x_center <= FINISH_ZONE[1][0]) and \
                       (FINISH_ZONE[0][1] <= y_center <= FINISH_ZONE[1][1]) and not car.finished:
                        current_time = time.time()
                        if current_time - car.last_lap_time > race_manager.cooldown_time:
                            car.increment_lap(current_time)

        current_time = time.time()
        for car in cars.values():
            color = car.color
            lap_pos = car.lap_position
            lap_complete_pos = car.lap_complete_position
            lap_time_diff = current_time - car.lap_text_start_time
            if lap_time_diff < LAP_COMPLETE_DURATION:
                lap_complete_pos_adjusted = (lap_complete_pos[0], lap_complete_pos[1] + 150)
                cv2.putText(new_frame, "Lap Complete", lap_complete_pos_adjusted,
                            FONT, FONT_SCALE_SIDEBAR, color, THICKNESS, LINE_TYPE)
                if car.lap_times:
                    last_lap_time = car.lap_times[-1]
                    if last_lap_time > 0:
                        last_minutes, last_seconds = divmod(last_lap_time, 60)
                        lap_time_text = f"{int(last_minutes)}m {last_seconds:.2f}s"
                        lap_time_pos = (lap_complete_pos_adjusted[0], lap_complete_pos_adjusted[1] + 30)
                        cv2.putText(new_frame, "Lap Time:", lap_time_pos, FONT, FONT_SCALE_SIDEBAR, color, THICKNESS, LINE_TYPE)
                        lap_time_value_pos = (lap_time_pos[0], lap_time_pos[1] + 25)
                        cv2.putText(new_frame, lap_time_text, lap_time_value_pos, FONT, FONT_SCALE_SIDEBAR, color, THICKNESS, LINE_TYPE)
            if race_manager.race_start_time is not None:
                total_race_time = car.get_total_race_time(race_manager.race_start_time, current_time)
                total_minutes, total_seconds = divmod(total_race_time, 60)
                total_time_label = "Total Time:"
                total_time_value = f"{int(total_minutes)}m {total_seconds:.2f}s"
            else:
                total_time_label = "Total Time:"
                total_time_value = "N/A"
            best_lap_time = car.get_best_lap_time()
            if best_lap_time is not None:
                best_minutes, best_seconds = divmod(best_lap_time, 60)
                best_lap_label = "Fastest Lap:"
                best_lap_value = f"{int(best_minutes)}m {best_seconds:.2f}s"
            else:
                best_lap_label = "Fastest Lap:"
                best_lap_value = "N/A"
            if car.finished:
                cv2.putText(new_frame, "Finished", lap_pos, FONT, FONT_SCALE_SIDEBAR, color, THICKNESS, LINE_TYPE)
            else:
                lap_text = f"Lap: {car.lap_count}"
                cv2.putText(new_frame, lap_text, lap_pos, FONT, FONT_SCALE_SIDEBAR, color, THICKNESS, LINE_TYPE)
            total_time_label_pos = (lap_pos[0], lap_pos[1] + 35)
            total_time_value_pos = (lap_pos[0], total_time_label_pos[1] + 25)
            best_lap_label_pos = (lap_pos[0], total_time_value_pos[1] + 35)
            best_lap_value_pos = (lap_pos[0], best_lap_label_pos[1] + 25)
            cv2.putText(new_frame, total_time_label, total_time_label_pos, FONT, FONT_SCALE_SIDEBAR, color, THICKNESS, LINE_TYPE)
            cv2.putText(new_frame, total_time_value, total_time_value_pos, FONT, FONT_SCALE_SIDEBAR, color, THICKNESS, LINE_TYPE)
            cv2.putText(new_frame, best_lap_label, best_lap_label_pos, FONT, FONT_SCALE_SIDEBAR, color, THICKNESS, LINE_TYPE)
            cv2.putText(new_frame, best_lap_value, best_lap_value_pos, FONT, FONT_SCALE_SIDEBAR, color, THICKNESS, LINE_TYPE)

        new_frame = draw_ranking_bar(new_frame, list(cars.values()), RANKING_BAR_CONFIG)

        if race_manager.race_started and (time.time() - race_manager.race_start_time < 1):
            go_position = (new_frame.shape[1] // 2 - GO_TEXT_OFFSET_X, new_frame.shape[0] // 2 + GO_TEXT_OFFSET_Y)
            cv2.putText(new_frame, GO_TEXT, go_position, FONT, GO_TEXT_FONT_SCALE, GO_TEXT_COLOR, GO_TEXT_THICKNESS, LINE_TYPE)

        cv2.imshow("ArUco Auto Tracken met Ronde Detectie", new_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('r'):
            race_manager.reset_race()
            for car in cars.values():
                car.reset()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
