# Main.py

import cv2
import numpy as np
import threading
import tkinter as tk
import signal

from config import *
from car_utils import initialize_cars
from race_manager import RaceManager
from path_utils import expand_path
from race_logic import process_frame, run_race
from menu_to_race import RaceMenu


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

    # Start de race
    run_race(cap, cars, race_manager)

    # Zorg ervoor dat de camera netjes wordt vrijgegeven en vensters worden gesloten.
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()