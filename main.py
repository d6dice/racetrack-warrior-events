import cv2
import threading
import tkinter as tk
import signal
import logging
from tkinter import messagebox

from config import *
from car_utils import initialize_cars
from race_manager import RaceManager
from race_logic import initialize_frame, run_race
from race_menu import RaceMenu
from image_utils import display_camera_feed

# Stel logging in
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_close(sig, frame):
    logging.info("Programma wordt afgesloten...")
    cv2.destroyAllWindows()
    exit(0)

signal.signal(signal.SIGINT, handle_close)
signal.signal(signal.SIGTERM, handle_close)

def main():
    logging.info("main() is gestart!")

    # Open een Tkinter venster voor het menu
    root = tk.Tk()
    logging.info("Tkinter venster geopend!")
    race_menu = RaceMenu(root)
    logging.info("RaceMenu geïnitialiseerd!")

    # Initialiseer gedeelde resources
    race_manager = RaceManager()
    cars = {}
    stop_event = threading.Event()
    frame_lock = threading.Lock()
    shared_frame = [None]  # Gebruik een lijst voor een gedeelde mutable buffer

    # Open de camera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        messagebox.showerror("Fout", "Kan de camera niet openen. Controleer de verbinding.")
        logging.error("❌ Kan de camera niet openen.")
        return

    logging.info("Camera geopend bij opstarten!")

    # Lees het eerste frame en initialiseer de overlay
    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Fout", "Kan geen frame lezen van de camera.")
        logging.error("❌ Kan geen frame lezen van de camera.")
        return

    base_overlay = initialize_frame(frame, cars, race_manager)

    # Start camera feed thread
    camera_thread = threading.Thread(target=display_camera_feed, args=(cap, stop_event, base_overlay, shared_frame, frame_lock), daemon=True)
    camera_thread.start()

    def start_race():
        logging.info("Gebruiker heeft 'Start Race' geklikt.")
        participating_cars = []
        for color, username in race_menu.auto_data.items():
            logging.debug(f"Auto kleur: {color}, Gebruiker: {username.get()}")

            mapped_color = COLOR_MAPPING.get(color.lower())
            if mapped_color and username.get().strip():
                participating_cars.append({"color": mapped_color, "username": username.get()})

        if not participating_cars:
            messagebox.showerror("Fout", "Je moet ten minste één auto selecteren om de race te starten!")
            logging.error("❌ Geen auto's geselecteerd.")
            return

        logging.info(f"Deelnemende auto's: {participating_cars}")

        cars.update(initialize_cars(participating_cars))
        for marker_id, car in cars.items():
            logging.info(f"✅ Auto {marker_id}: color_key = {car.color_key}, color = {car.color}, username = {car.username}")

        stop_event.clear()
        race_thread = threading.Thread(
            target=run_race,
            args=(cars, race_manager, cap, stop_event, shared_frame, frame_lock),
            daemon=True
        )
        race_thread.start()
        logging.info("Thread voor run_race succesvol gestart!")

    def reset_race():
        logging.info("Gebruiker heeft 'Reset' geklikt. Race wordt gereset.")
        stop_event.set()
        race_manager.reset()
        for car in cars.values():
            car.reset()
        messagebox.showinfo("Reset", "De race is gereset. Je kunt opnieuw beginnen door op 'Start Race' te klikken.")

    # Tkinter afsluitlogica
    def on_close():
        stop_event.set()
        cap.release()
        cv2.destroyAllWindows()
        root.destroy()

    race_menu.start_button.config(command=start_race)
    race_menu.reset_button.config(command=reset_race)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    logging.info("Tkinter event loop beëindigd!")


if __name__ == '__main__':
    logging.info("main() wordt aangeroepen!")
    main()