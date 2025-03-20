from config import CAR_IMAGES
from image_utils import load_image
import time


# car.py
import time

class Car:
    def __init__(self, marker_id, color, car_image, lap_position, lap_complete_position, color_key):
        """
        Initialiseer een Car-object.

        Args:
            marker_id (int): De unieke marker-ID voor de auto.
            color (tuple): De kleur (BGR) die gebruikt kan worden voor overlays.
            car_image (numpy.ndarray): De afbeelding van de auto.
            lap_position (tuple): De positie-offset voor de basisinformatie in de zijbalk.
            lap_complete_position (tuple): De positie-offset voor de "Lap Complete"-melding.
            color_key (str): De sleutel om de gewenste tekstkleur op te halen uit de configuratie.
        """
        self.marker_id = marker_id
        self.color = color
        self.car_image = car_image
        self.lap_position = lap_position
        self.lap_complete_position = lap_complete_position
        self.color_key = color_key  # Zorg dat dit wordt opgeslagen

        # Andere attributen in de Car-klasse
        self.x = None
        self.y = None
        self.display_x = None
        self.display_y = None
        self.scale_factor = 1.0
        self.lap_count = 0
        self.lap_times = []  # Lijst met lap-tijden
        self.fastest_lap = None  # Voeg dit attribuut toe zodat get_best_lap_time() hier op kan werken
        self.finished = False
        self.progress = 0.0
        self.last_lap_time = 0.0
        self.lap_text_start_time = time.time()
        self.position = None
        self.final_position = None  # Nieuw attribuut: final finish ranking
        
    def update_position(self, x, y, scale_factor):
            self.x = x
            self.y = y
            self.scale_factor = scale_factor    

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


    def increment_lap(self, current_time, total_laps, race_manager):  
        if self.last_lap_time is not None:
            lap_time = current_time - self.last_lap_time
            if hasattr(self, 'fastest_lap'):
                if self.fastest_lap is None or lap_time < self.fastest_lap:
                    self.fastest_lap = lap_time
            else:
                self.fastest_lap = lap_time
        else:
            self.last_lap_time = current_time

        self.lap_count += 1
        self.last_lap_time = current_time

        if self.lap_count >= total_laps and not self.finished:
            self.finished = True
            self.finish_time = current_time
            # Als de auto net is gefinished, stel dan haar final finish order in.
            # We gebruiken hiervoor een attribute in race_manager, bijvoorbeeld finished_order (zie RaceManager hieronder)
            if hasattr(race_manager, "finished_order"):
                race_manager.finished_order.append(self.marker_id)
                self.final_position = len(race_manager.finished_order)
            else:
                self.final_position = 1  # fallback

    def get_best_lap_time(self):
        """
        Retourneert de snelste laptijd als er een gemeten is, anders None.
        """
        return self.fastest_lap

    def reset(self):
        """
        Reset alle dynamische racegegevens van de auto.
        """
        self.x = None
        self.y = None
        self.display_x = None
        self.display_y = None
        self.scale_factor = 1.0
        self.lap_count = 0
        self.progress = 0.0
        self.position = None
        self.last_lap_time = 0.0
        self.finished = False
        self.finish_time = None
        self.fastest_lap = None
        self.final_position = None