print("main.py wordt uitgevoerd!")  # Debug-uitvoer

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
from race_menu import RaceMenu

# master branch goed werkende code
def handle_close(sig, frame):
    """
    Zorgt voor een nette afsluiting van het programma.
    """
    print("Programma wordt afgesloten...")
    cv2.destroyAllWindows()
    exit(0)


# Registreer de signalen voor een nette afsluiting
signal.signal(signal.SIGINT, handle_close)
signal.signal(signal.SIGTERM, handle_close)

def main():
    print("main() is gestart!")  # Debug-uitvoer

    # Open een Tkinter venster voor het menu
    root = tk.Tk()
    print("Tkinter venster geopend!")  # Debug-uitvoer
    race_menu = RaceMenu(root)
    print("RaceMenu geïnitialiseerd!")  # Debug-uitvoer

    # Initialiseer race manager op hoog niveau
    race_manager = RaceManager()

    def start_race():
        print("Gebruiker heeft 'Start Race' geklikt.")  # Debug-uitvoer

        # Haal de gebruikersnamen en deelnemende auto's op uit het menu
        participating_cars = []
        for color, username in race_menu.auto_data.items():
            print(f"Auto kleur: {color}, Gebruiker: {username.get()}")  # Debug-uitvoer

            # Gebruik de mapping om de kleur om te zetten
            mapped_color = COLOR_MAPPING.get(color.lower())
            if mapped_color and username.get().strip():
                participating_cars.append({"color": mapped_color, "username": username.get()})

        # Controleer of er deelnemende auto's zijn
        if not participating_cars:
            print("❌ Geen auto's geselecteerd. Het programma wordt afgesloten.")
            return

        print("Deelnemende auto's:", participating_cars)  # Debug-uitvoer

        # Initialiseer auto's
        cars = initialize_cars(participating_cars)
        for marker_id, car in cars.items():
            print(f"✅ Auto {marker_id}: color_key = {car.color_key}, color = {car.color}, username = {car.username}")

        # Open de camera
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            print("❌ Kan de camera niet openen.")
            return

        print("Camera geopend!")  # Debug-uitvoer

        # Debug-uitvoer vóór het starten van de thread
        print("Thread wordt aangemaakt voor run_race...")  # Debug-uitvoer

        # Start de race-logica in een aparte thread
        thread = threading.Thread(target=lambda: run_race(cars, race_manager, cap), daemon=True)
        thread.start()

        # Debug-uitvoer na het starten van de thread
        print("Thread voor run_race succesvol gestart!")  # Debug-uitvoer

        # Sluit het menu
        root.destroy()

    # Voeg de startknop-functionaliteit toe
    race_menu.start_button.config(command=start_race)

    root.mainloop()
    print("Tkinter event loop beëindigd!")  # Debug-uitvoer


if __name__ == '__main__':
    print("main() wordt aangeroepen!")  # Debug-uitvoer
    main()