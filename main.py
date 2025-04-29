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
from race_logic import process_frame
from race_menu import RaceMenu


def handle_close(sig, frame):
    print("Programma wordt afgesloten...")
    cv2.destroyAllWindows()
    exit(0)

signal.signal(signal.SIGINT, handle_close)
signal.signal(signal.SIGTERM, handle_close)

def run_race(cars, race_manager, cap):
    """
    Logica om de race te runnen.
    """
    # Definieer het ArUco-dictionary en de detectieparameters
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()

    # Maak het uitgezette pad (expanded_path) voor het parcours
    expanded_path = expand_path(PATH_POINTS, width=PATH_WIDTH)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("⚠️ Geen frame ontvangen van de camera. Controleer de verbinding.")
            continue

        # Debug: Log frame-informatie
        print(f"✅ Frame ontvangen. Afmetingen: {frame.shape}")

        # Detecteer ArUco-markers
        corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
        if ids is not None:
            print(f"✅ Gedetecteerde markers: {ids.flatten()}")
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)  # Teken gedetecteerde markers op het frame
        else:
            print("⚠️ Geen ArUco-markers gedetecteerd.")

        # Fallback-logica voor auto's zonder posities
        for car_id, car in cars.items():
            if car.x is None or car.y is None:
                print(f"⚠️ Auto {car.color_key} heeft geen geldige positie. Standaardwaarden ingesteld.")
                car.x, car.y = 0, 0  # Standaardpositie

        # Verwerk het frame: Dit omvat het tekenen van het parcours, finish-zone, countdown, marker-detectie, en overlays
        try:
            processed_frame = process_frame(frame, race_manager, cars, parameters, aruco_dict, expanded_path)
        except Exception as e:
            print(f"❌ Fout bij verwerken frame: {e}")
            continue

        # Toon het verwerkte frame
        cv2.imshow("ArUco Auto Tracken met Ronde Detectie", processed_frame)

        # Controleer het sluiten van het venster en toetsen
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or cv2.getWindowProperty("ArUco Auto Tracken met Ronde Detectie", cv2.WND_PROP_VISIBLE) < 1:  # 27 is de ASCII-code voor Esc
            print("Programma wordt afgesloten...")
            break

    # Zorg ervoor dat de camera netjes wordt vrijgegeven en vensters worden gesloten
    cap.release()
    cv2.destroyAllWindows()

def main():
    # Open de camera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("❌ Kan de camera niet openen.")
        return

    # Open een Tkinter venster voor het menu
    root = tk.Tk()
    race_menu = RaceMenu(root)

    def start_race():
        # Haal de gebruikersnamen en deelnemende auto's op uit het menu
        participating_cars = []
        for color, username in race_menu.auto_data.items():
            # Gebruik de mapping om de kleur om te zetten
            mapped_color = COLOR_MAPPING.get(color.lower())
            if mapped_color and username.get().strip():
                participating_cars.append({"color": mapped_color, "username": username.get()})

        # Controleer of er deelnemende auto's zijn
        if not participating_cars:
            print("❌ Geen auto's geselecteerd. Het programma wordt afgesloten.")
            return

        # Initialiseer auto's en de race manager
        cars = initialize_cars(participating_cars)
        for marker_id, car in cars.items():
            print(f"✅ Auto {marker_id}: color_key = {car.color_key}, color = {car.color}, username = {car.username}")

        # Start de race-logica in een aparte thread
        race_manager = RaceManager()
        threading.Thread(target=lambda: run_race(cars, race_manager, cap), daemon=True).start()

        # Start de countdown direct
        race_manager.start_countdown()

        # Sluit het menu
        root.destroy()

    # Voeg de startknop-functionaliteit toe
    race_menu.start_button.config(command=start_race)

    root.mainloop()


if __name__ == '__main__':
    main()