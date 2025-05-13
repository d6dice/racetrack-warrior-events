import cv2
import numpy as np
import threading
import tkinter as tk
import signal
import logging
from tkinter import messagebox

from config import *
from car_utils import initialize_cars
from race_manager import RaceManager
from path_utils import expand_path
from race_logic import process_frame, run_race
from race_menu import RaceMenu

# Stel logging in
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def handle_close(sig, frame):
    """
    Zorgt voor een nette afsluiting van het programma.
    """
    logging.info("Programma wordt afgesloten...")
    cv2.destroyAllWindows()
    exit(0)


# Registreer de signalen voor een nette afsluiting
signal.signal(signal.SIGINT, handle_close)
signal.signal(signal.SIGTERM, handle_close)


def main():
    logging.info("main() is gestart!")

    # Open een Tkinter venster voor het menu
    root = tk.Tk()
    logging.info("Tkinter venster geopend!")
    race_menu = RaceMenu(root)
    logging.info("RaceMenu geïnitialiseerd!")

    # Initialiseer race manager op hoog niveau
    race_manager = RaceManager()
    cars = {}  # Auto's worden pas geïnitialiseerd bij het starten van de race
    stop_event = threading.Event()  # Gebruik een event voor nette thread-afhandeling
    thread = None    

    def start_race():
        
        
        logging.info("Gebruiker heeft 'Start Race' geklikt.")

        # Haal de gebruikersnamen en deelnemende auto's op uit het menu
        participating_cars = []
        for color, username in race_menu.auto_data.items():
            logging.debug(f"Auto kleur: {color}, Gebruiker: {username.get()}")

            # Gebruik de mapping om de kleur om te zetten
            mapped_color = COLOR_MAPPING.get(color.lower())
            if mapped_color and username.get().strip():
                participating_cars.append({"color": mapped_color, "username": username.get()})

        # Controleer of er deelnemende auto's zijn
        if not participating_cars:
            messagebox.showerror("Fout", "Je moet ten minste één auto selecteren om de race te starten!")
            logging.error("❌ Geen auto's geselecteerd. Het programma wordt afgesloten.")
            return

        logging.info(f"Deelnemende auto's: {participating_cars}")

        # Initialiseer auto's
        cars = initialize_cars(participating_cars)
        for marker_id, car in cars.items():
            logging.info(f"✅ Auto {marker_id}: color_key = {car.color_key}, color = {car.color}, username = {car.username}")

        # Open de camera
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            messagebox.showerror("Fout", "Kan de camera niet openen. Controleer de verbinding.")
            logging.error("❌ Kan de camera niet openen.")
            return

        logging.info("Camera geopend!")

        # Debug-uitvoer vóór het starten van de thread
        logging.debug("Thread wordt aangemaakt voor run_race...")

        # Stop Event voor nette thread beëindiging
        stop_event = threading.Event()

        # Start de race-logica in een aparte thread
        thread = threading.Thread(target=lambda: run_race(cars, race_manager, cap, stop_event), daemon=True)
        thread.start()

        # Debug-uitvoer na het starten van de thread
        logging.info("Thread voor run_race succesvol gestart!")
        
    def reset_race():
        nonlocal thread, cars

        logging.info("Gebruiker heeft 'Reset' geklikt. Race wordt gereset.")

        # Stop de huidige race als die draait
        if thread and thread.is_alive():
            stop_event.set()
            thread.join()
            logging.info("Huidige race-thread gestopt.")

        # Reset RaceManager en auto's
        race_manager.reset()
        for car in cars.values():
            car.reset()

        # Informeer de gebruiker
        messagebox.showinfo("Reset", "De race is gereset. Je kunt opnieuw beginnen door op 'Start Race' te klikken.")

    # Voeg de functionaliteit toe aan de knoppen
    race_menu.start_button.config(command=start_race)
    race_menu.reset_button.config(command=reset_race)    

    # Zorg voor nette afsluiting van de thread
    def on_close():
        # Zorg ervoor dat de thread netjes stopt bij afsluiten
        stop_event.set()
        if thread:
            thread.join()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    logging.info("Tkinter event loop beëindigd!")


if __name__ == '__main__':
    logging.info("main() wordt aangeroepen!")
    main()