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
        """
        Initialiseert de RaceManager met de gegeven countdown- en cooldown-durations.
        De race wordt standaard niet gestart.
        """
        self.countdown_duration = countdown_duration
        self.cooldown_time = cooldown_time
        self.race_started = False
        self.countdown_start_time = None
        self.race_start_time = None
        self.finished_order = []  # Nieuw: opslaan in welke volgorde auto's finishen

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

    def start_race(self):
        """
        Start de race:
          - Zet 'race_started' op True.
          - Leg het tijdstip van de start vast in 'race_start_time'.
          - Reset de countdown (countdown_start_time wordt op None gezet).
        """
        self.race_started = True
        self.race_start_time = time.time()
        self.countdown_start_time = None

    def reset_race(self):
        """
        Reset alle race-gerelateerde attributen zodat een nieuwe race kan beginnen.
        Hierdoor worden de waarden voor race_start_time en countdown_start_time leeggemaakt,
        en wordt race_started terug op False gezet.
        """
        self.race_started = False
        self.countdown_start_time = None
        self.race_start_time = None
