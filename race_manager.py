
import cv2
import numpy as np
import time

class RaceManager:
    """
    Beheert de status van de race, inclusief countdown, start en reset.

    Attributen:
        countdown_duration (float): Duur (in seconden) waarop geteld wordt vóór de start van de race.
        cooldown_time (float): Minimale tijd (in seconden) tussen het registreren van lappen (optioneel voor lap-regeling).
        race_started (bool): Geeft aan of de race is gestart.
        countdown_start_time (float of None): Het tijdstip waarop de countdown is gestart; 
                                               als dit None is, is de countdown nog niet begonnen.
        race_start_time (float of None): Het tijdstip waarop de race daadwerkelijk is gestart.
    """
    
    def __init__(self, countdown_duration=3, cooldown_time=2):
        # Initialiseer race-gerelateerde attributen
        self.countdown_duration = countdown_duration
        self.cooldown_time = cooldown_time
        self.race_started = False
        self.countdown_start_time = None
        self.race_start_time = None
        self.cars = []  # Lijst met deelnemende auto's
        self.finished_order = []  # Opslaan in welke volgorde auto's finishen
        print("RaceManager is geïnitialiseerd!")  # Debug

    def start_countdown(self):
        """
        Start de countdown voor de race als deze nog niet actief is.
        Dit stelt de variable 'countdown_start_time' in op de huidige tijd.
        """        
        if self.countdown_start_time is None:
            self.countdown_start_time = time.time()

    def update_countdown(self):
        """
        Berekent de resterende countdown-tijd.

        Returns:
            int of None:
              - Als de countdown actief is, wordt de resterende tijd (in seconden) teruggegeven. 
                Hierbij wordt naar boven afgerond zodat er altijd een integer is die even wat
                boven nul ligt zolang de countdown nog loopt.
              - Als de countdown nog niet gestart is, wordt None teruggegeven.
              - Als de countdown afgelopen is, wordt 0 teruggegeven.
        """
        if self.countdown_start_time is None:
            return None  # Countdown is niet gestart

        elapsed = time.time() - self.countdown_start_time
        remaining = self.countdown_duration - elapsed

        if remaining > 0:
            # Rond naar boven: als er nog een fractie overblijft, verhogen we met 1 
            return int(remaining) + (1 if remaining % 1 > 0 else 0)
        else:
            return 0

    def start_race(self, participating_cars=None):
        """
        Start de race en initialiseert de deelnemende auto's.
        """
        if participating_cars is None:
            participating_cars = []  # Standaard naar een lege lijst
        print("Start Race wordt aangeroepen!")  # Debug
        self.cars = participating_cars  # Voeg de deelnemende auto's toe
        self.race_started = True
        self.race_start_time = time.time()
        self.countdown_start_time = None
        print(f"Race gestart met {len(self.cars)} auto's!")  # Debug

    def reset(self):
        """
        Reset de race volledig.
        """
        print("RaceManager reset wordt aangeroepen!")  # Debug
        self.race_started = False
        self.countdown_start_time = None
        self.race_start_time = None
        self.finished_order = []
        self.cars = []  # Reset de lijst met auto's

        # Reset alle auto's
        for car in self.cars:
            car.reset()
        print("Alle auto's zijn gereset!")  # Debug
        print("RaceManager is volledig gereset!")  # Debug