#race_manager.py

import time

class RaceManager:
    """
    Beheert de status van de race, inclusief countdown, start en reset.

    Attributen:
        countdown_duration (float): Duur (in seconden) van de countdown vóór de race.
        cooldown_time (float): Minimale tijd (in seconden) tussen het registreren van lappen.
        race_started (bool): Geeft aan of de race gestart is.
        countdown_start_time (float of None): Tijdstip waarop de countdown is gestart.
        race_start_time (float of None): Tijdstip waarop de race is gestart.
    """
    
    def __init__(self, countdown_duration=3, cooldown_time=2):
        self.countdown_duration = countdown_duration
        self.cooldown_time = cooldown_time
        self.race_started = False
        self.countdown_start_time = None
        self.race_start_time = None

    def start_countdown(self):
        """
        Start de countdown voor de race, mits deze nog niet loopt.
        """
        if self.countdown_start_time is None:
            self.countdown_start_time = time.time()

    def update_countdown(self):
        """
        Bereken en geef de resterende countdown-tijd terug.

        Returns:
            int of None: 
                - Als er een countdown actief is, retourneert deze de resterende seconden.
                - Als de countdown nog niet gestart is, retourneert None.
                - Als de countdown afgerond is, geeft het 0 terug.
        """
        if self.countdown_start_time is None:
            return None

        elapsed = time.time() - self.countdown_start_time
        remaining = self.countdown_duration - elapsed

        if remaining > 0:
            # Om een zichtbare countdown te creëren, ronden we altijd naar boven.
            return int(remaining) + (1 if remaining - int(remaining) > 0 else 0)
        else:
            return 0

    def start_race(self):
        """
        Start de race door de race_started vlag op True te zetten en het starttijdstip vast te leggen.
        Reset tevens de countdown.
        """
        self.race_started = True
        self.race_start_time = time.time()
        self.countdown_start_time = None

    def reset_race(self):
        """
        Reset alle racegerelateerde attributen zodat een nieuwe race gestart kan worden.
        """
        self.race_started = False
        self.countdown_start_time = None
        self.race_start_time = None
