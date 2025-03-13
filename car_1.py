# car.py

import time
from config_1 import LAP_COMPLETE_DURATION

class Car:
    def __init__(self, marker_id, color, car_image, lap_position, lap_complete_position):
        self.marker_id = marker_id
        self.color = color
        self.car_image = car_image
        self.lap_position = lap_position
        self.lap_complete_position = lap_complete_position
        self.lap_count = 1
        self.lap_times = []
        self.last_lap_time = 0
        self.lap_text_start_time = 0
        self.finished = False

    def update_position(self, x_center, y_center, scale_factor):
        self.x_center = x_center
        self.y_center = y_center
        self.scale_factor = scale_factor

    def increment_lap(self, current_time):
        self.lap_count += 1
        lap_time = current_time - self.last_lap_time
        if lap_time > 0:
            self.lap_times.append(lap_time)
        else:
            self.lap_times.append(0)
        self.last_lap_time = current_time
        self.lap_text_start_time = current_time
        if self.lap_count >= 4:
            self.finished = True

    def get_best_lap_time(self):
        positive_lap_times = [t for t in self.lap_times if t > 0]
        if positive_lap_times:
            return min(positive_lap_times)
        else:
            return None

    def get_total_race_time(self, race_start_time, current_time):
        if self.finished:
            return self.last_lap_time - race_start_time
        else:
            return current_time - race_start_time

    def reset(self):
        self.lap_count = 1
        self.lap_times = []
        self.last_lap_time = 0
        self.lap_text_start_time = 0
        self.finished = False
