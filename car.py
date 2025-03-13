#car.py

import time

class Car:
    def __init__(self, marker_id, color, car_image, lap_position=None, lap_complete_position=None):
        """
        Initialiseert een Car-object met de benodigde eigenschappen.

        Args:
            marker_id (int): De unieke marker-ID die deze auto representeert.
            color (tuple): De kleur (B, G, R) voor tekst en overlays.
            car_image (numpy.ndarray): De afbeelding van de auto.
            lap_position (tuple, optional): De positie (x, y) waar de lap-informatie wordt getoond.
            lap_complete_position (tuple, optional): De positie (x, y) voor de 'Lap Complete'-melding.
        """
        self.marker_id = marker_id
        self.color = color
        self.car_image = car_image
        self.lap_position = lap_position
        self.lap_complete_position = lap_complete_position

        # Positie en schaal van de auto op het frame
        self.x = None
        self.y = None
        self.scale_factor = 1.0

        # Race tracking attributen
        self.lap_count = 0
        self.lap_times = []             # Lijst waarin de lap-tijden worden opgeslagen
        self.last_lap_time = 0.0        # Tijdstip van de laatste lap (wordt geüpdatet na elke voltooiing)
        self.lap_text_start_time = time.time()  # Starttijd van de lap (voor tijdelijke meldingen)
        self.finished = False           # Geeft aan of de auto de race heeft voltooid
        self.progress = 0.0             # Vooruitgang langs de centerline (wordt later berekend)
        self.position = None            # Race positie (bijv. 1 voor eerste, 2 voor tweede, etc.)

    def update_position(self, x, y, scale_factor):
        """
        Werk de positie en de schaal van de auto bij.

        Args:
            x (int): De nieuwe x-positie van de auto.
            y (int): De nieuwe y-positie van de auto.
            scale_factor (float): De schaalfactor voor het schalen van de auto-afbeelding.
        """
        self.x = x
        self.y = y
        self.scale_factor = scale_factor

    def increment_lap(self, current_time, total_laps):
        """
        Verhoogt het lap-nummer; slaat de lap-tijd op en markeert de auto als gefinished indien
        het totale aantal ronden is bereikt.

        Args:
            current_time (float): Huidige tijd (bijv. verkregen met time.time()).
            total_laps (int): Het totaal aantal te rijden rondes.
        """
        lap_time = current_time - self.last_lap_time
        self.lap_times.append(lap_time)
        self.lap_count += 1
        self.last_lap_time = current_time
        self.lap_text_start_time = current_time

        if self.lap_count >= total_laps:
            self.finished = True

    def reset(self):
        """
        Reset de race-gerelateerde attributen zodat een nieuwe race kan beginnen.
        """
        self.x = None
        self.y = None
        self.scale_factor = 1.0
        self.lap_count = 0
        self.lap_times = []
        self.last_lap_time = 0.0
        self.lap_text_start_time = time.time()
        self.finished = False
        self.progress = 0.0
        self.position = None

    def get_total_race_time(self, race_start_time, current_time):
        """
        Geeft de totale racetijd op basis van de starttijd en de huidige tijd.

        Args:
            race_start_time (float): Tijd waarop de race begon.
            current_time (float): De huidige tijd.

        Returns:
            float: De totale tijd van de race.
        """
        return current_time - race_start_time

    def get_best_lap_time(self):
        """
        Geeft de snelste lap-tijd terug (indien beschikbaar).

        Returns:
            float of None: De minimale lap-tijd indien er lap-tijden zijn, anders None.
        """
        if self.lap_times:
            return min(self.lap_times)
        return None
