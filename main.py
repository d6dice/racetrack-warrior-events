import threading
import cv2
import tkinter as tk
from tkinter import messagebox
from config import *
from car_utils import initialize_cars
from race_manager import RaceManager
from race_logic import initialize_frame, run_race
from race_menu import RaceMenu
from image_utils import display_camera_feed
import logging
import signal

# Belangrijk: pypylon importeren
from pypylon import pylon

# ========== UITLEG VAN DEZE VARIABELEN ==========
# camera_thread: de "draad" die de camerafeed toont
# camera: het Basler-camera-object van pypylon
# base_overlay: de basisafbeelding waarop de camera komt
# stop_event: een vlaggetje om threads netjes te laten stoppen
# shared_frame: gedeelde buffer voor frames tussen threads
# frame_lock: zorgt dat maar één thread tegelijk shared_frame mag aanpassen
camera_thread = None
camera = None
base_overlay = None

def handle_close(sig, frame):
    logging.info("Programma wordt afgesloten...")
    cv2.destroyAllWindows()
    if camera is not None:
        camera.Close()
    exit(0)

signal.signal(signal.SIGINT, handle_close)
signal.signal(signal.SIGTERM, handle_close)

def get_basler_frame(camera, converter):
    """Haalt één frame op van de Basler-camera en converteert deze naar een OpenCV-compatibel numpy-array."""
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    if grabResult.GrabSucceeded():
        image = converter.Convert(grabResult)
        frame = image.GetArray()
        grabResult.Release()
        return True, frame
    else:
        grabResult.Release()
        return False, None

def main():
    global camera_thread, camera, base_overlay

    logging.info("main() is gestart!")

    root = tk.Tk()
    logging.info("Tkinter venster geopend!")
    race_menu = RaceMenu(root)
    logging.info("RaceMenu geïnitialiseerd!")

    race_manager = RaceManager()
    cars = {}
    stop_event = threading.Event()
    frame_lock = threading.Lock()
    shared_frame = [None]

    # Basler-camera openen
    try:
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.Open()
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    except Exception as e:
        messagebox.showerror("Fout", f"Kan Basler-camera niet openen: {e}")
        logging.error(f"❌ Kan Basler-camera niet openen: {e}")
        return

    # Converter voor naar OpenCV-array
    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    logging.info("Basler-camera geopend bij opstarten!")
    ret, frame = get_basler_frame(camera, converter)
    if not ret:
        messagebox.showerror("Fout", "Kan geen frame lezen van de Basler-camera.")
        logging.error("❌ Kan geen frame lezen van de Basler-camera.")
        return

    base_overlay = initialize_frame(frame, cars, race_manager)

    # Start camera feed thread (ALLEEN BIJ OPSTARTEN)
    stop_event.clear()
    camera_thread = threading.Thread(
        target=display_camera_feed,
        args=(camera, converter, stop_event, base_overlay, shared_frame, frame_lock),
        daemon=True
    )
    camera_thread.start()

    def start_race():
        global camera_thread, base_overlay
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

        # ======= HIER ZORG JE DAT ER MAAR ÉÉN THREAD IS =======
        stop_event.set()    # Vraag de oude thread om te stoppen
        if camera_thread is not None:
            camera_thread.join()      # Wacht tot de oude thread echt klaar is

        cv2.destroyAllWindows()       # Sluit oude OpenCV-vensters
        stop_event.clear()            # Reset het stop-signaal voor de nieuwe thread

        # Nieuwe overlay voor de race:
        ret, frame = get_basler_frame(camera, converter)
        if not ret:
            messagebox.showerror("Fout", "Kan geen frame lezen van de Basler-camera.")
            logging.error("❌ Kan geen frame lezen van de Basler-camera.")
            return
        base_overlay = initialize_frame(frame, cars, race_manager)

        # Start nieuwe camera-thread voor de race
        camera_thread = threading.Thread(
            target=display_camera_feed,
            args=(camera, converter, stop_event, base_overlay, shared_frame, frame_lock),
            daemon=True
        )
        camera_thread.start()

        # Start nu de race-thread zoals je gewend bent
        race_thread = threading.Thread(
            target=run_race,
            args=(cars, race_manager, camera, converter, stop_event, shared_frame, frame_lock),
            daemon=True
        )
        race_thread.start()
        logging.info("Thread voor run_race succesvol gestart!")

    def reset_race():
        global camera_thread, base_overlay
        logging.info("Gebruiker heeft 'Reset' geklikt. Race wordt gereset.")
        stop_event.set()
        if camera_thread is not None:
            camera_thread.join()
        cv2.destroyAllWindows()
        stop_event.clear()
        # Je kunt hier desgewenst opnieuw de overlay en de camera-thread starten als je dat wilt,
        # of gewoon wachten tot de gebruiker weer op start drukt.

    # Koppel deze functies aan je menu/knoppen
    race_menu.set_start_callback(start_race)
    race_menu.set_reset_callback(reset_race)

    root.mainloop()

    # Camera netjes afsluiten na afloop
    if camera is not None:
        camera.Close()

if __name__ == "__main__":
    main()