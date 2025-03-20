#car_utils

import cv2
import numpy as np

from config import CAR_IMAGES, CAR_TEXT_POSITIONS, SIDEBAR_TEXT_COLORS, DEFAULT_USERNAMES
from car import Car
from image_utils import load_image


def initialize_cars():
    cars = {}
    try:
        for car_key, car_config in CAR_IMAGES.items():
            car_image = load_image(car_config["path"], car_config["width"], car_config["height"])
            
            # Haal standaarden op: kleur uit SIDEBAR_TEXT_COLORS en een default username (kan gedefinieerd zijn in je config)
            color = SIDEBAR_TEXT_COLORS.get(car_key, (255, 255, 255))
            default_username = DEFAULT_USERNAMES.get(car_key, car_key.capitalize())
            default_color_name = car_key.capitalize()
            
            # Haal positie-offsets op uit CAR_TEXT_POSITIONS
            lap_pos = CAR_TEXT_POSITIONS[car_key]["lap_position_offset"]
            lap_complete_pos = CAR_TEXT_POSITIONS[car_key]["lap_complete_position_offset"]            
            
            car = Car(
                marker_id = len(cars),
                color = color,
                car_image = car_image,
                lap_position = CAR_TEXT_POSITIONS[car_key]["lap_position_offset"],
                lap_complete_position = CAR_TEXT_POSITIONS[car_key]["lap_complete_position_offset"],
                color_key = car_key
            )
            car.username = default_username        # Voorlopige (default) gebruikersnaam
            car.color_name = default_color_name      # Voorlopige kleurnaam
            cars[len(cars)] = car
    except Exception as e:
        print(f"Fout bij het initialiseren van auto's: {e}")
    return cars
