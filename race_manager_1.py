# race_manager.py

import time
from config_1 import COOLDOWN_TIME

class RaceManager:
    def __init__(self):
        self.race_started = False
        self.race_start_time = None
        self.countdown_start_time = None
        self.countdown_number = None
        self.cooldown_time = COOLDOWN_TIME

    def start_countdown(self):
        self.countdown_start_time = time.time()
        self.countdown_number = 3
        print("Countdown gestart.")

    def update_countdown(self):
        if self.countdown_number is not None:
            time_since_countdown_start = time.time() - self.countdown_start_time
            if time_since_countdown_start >= 1:
                self.countdown_number -= 1
                self.countdown_start_time = time.time()
            return self.countdown_number
        return None

    def start_race(self):
        self.race_started = True
        self.race_start_time = time.time()
        self.countdown_number = None
        print("Race gestart.")  # Debugging: Race gestart

    def reset_race(self):
        self.__init__()  # Reset alle attributen naar beginwaarden
        print("Race reset.")  # Debugging: Race reset
