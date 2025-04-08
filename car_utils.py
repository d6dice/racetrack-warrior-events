#car_utils

import cv2
import numpy as np

from config import CAR_CONFIG
from car import Car
from image_utils import load_image


def initialize_cars():
    cars = {}
    try:
        # Itereer over elke auto in de centrale CAR_CONFIG
        for car_key, settings in CAR_CONFIG.items():
            # Laad de auto-afbeelding op basis van de opgegeven path en afmetingen
            car_image = load_image(settings["image_path"], settings["width"], settings["height"])

            # Haal de relevante instellingen op direct uit de CAR_CONFIG entry
            color = settings["sidebar_text_color"]
            default_username = settings["username"]
            # Gebruik de offsets voor lap en lap complete
            lap_pos = settings["lap_position_offset"]
            lap_complete_pos = settings["lap_complete_position_offset"]

            # Maak een nieuw Car-object aan.
            # Gebruik de marker_id uit de config zodat dit consistent is met de ArUco-marker.
            car = Car(
                marker_id=settings["marker_id"],
                color=color,
                car_image=car_image,
                lap_position=lap_pos,
                lap_complete_position=lap_complete_pos,
                color_key=car_key
            )
            # Stel het username en de (default) kleurnaam in
            car.username = default_username
            car.color_name = car_key.capitalize()

            # Sla de auto op in de 'cars' dictionary met key als marker_id voor snelle lookup
            cars[settings["marker_id"]] = car
    except Exception as e:
        print(f"Fout bij het initialiseren van auto's: {e}")
    return cars
