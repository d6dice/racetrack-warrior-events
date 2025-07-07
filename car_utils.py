# car_utils

import cv2
import numpy as np

from config import CAR_CONFIG
from car import Car
from image_utils import load_image


def initialize_cars(participating_cars):
    """
    Initialiseer de auto's op basis van de configuratie en de lijst van deelnemende auto's.
    
    :param participating_cars: Een lijst van dictionaries met de deelnemende auto's (kleur en gebruikersnaam).
    :return: Een dictionary met Car-objecten, waarbij de sleutels de marker_id's zijn.
    """
    cars = {}
    try:
        # Itereer over de deelnemende auto's
        for car_info in participating_cars:
            color_key = car_info["color"]
            username = car_info["username"]

            # Haal de instellingen op uit de CAR_CONFIG
            if color_key not in CAR_CONFIG:
                print(f"Waarschuwing: Auto met kleur '{color_key}' niet gevonden in CAR_CONFIG.")
                continue

            settings = CAR_CONFIG[color_key]

            # Laad de auto-afbeelding op basis van de opgegeven path en afmetingen
            car_image = load_image(settings["image_path"], settings["width"], settings["height"])

            # Haal de relevante instellingen op direct uit de CAR_CONFIG entry
            color = settings["sidebar_text_color"]
            lap_pos = settings["lap_position_offset"]
            lap_complete_pos = settings["lap_complete_position_offset"]

            # Maak een nieuw Car-object aan
            car = Car(
                marker_id=settings["marker_id"],
                color=color,
                car_image=car_image,
                lap_position=lap_pos,
                lap_complete_position=lap_complete_pos,
                color_key=color_key
            )
            # Stel de gebruikersnaam in vanuit het menu
            car.username = username
            car.color_name = color_key.capitalize()

            # Sla de auto op in de 'cars' dictionary met key als marker_id voor snelle lookup
            cars[settings["marker_id"]] = car
    except Exception as e:
        print(f"Fout bij het initialiseren van auto's: {e}")
    return cars


def update_car_usernames(usernames):
    """
    Werk de gebruikersnamen in CAR_CONFIG bij op basis van de invoer uit het menu.
    
    :param usernames: Dict met keys als 'blue_car', 'green_car', etc., en de bijbehorende gebruikersnamen.
    """
    for car_key, username in usernames.items():
        if car_key in CAR_CONFIG:
            CAR_CONFIG[car_key]["username"] = username
            