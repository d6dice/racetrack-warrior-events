from config import PATH_POINTS
from path_utils import compute_cumulative_distances, calculate_progress_distance
from tracking_utils import project_to_centerline

def sort_cars_by_position(cars):
    # Jouw complete implementatie
    cum = compute_cumulative_distances(PATH_POINTS)
    total_distance = cum[-1]
    
    start_point = (350, 50)
    start_offset = project_to_centerline(start_point, PATH_POINTS)
    
    for car in cars.values():
        if car.x is not None and car.y is not None:
            raw_progress = calculate_progress_distance(car, PATH_POINTS)
            car.progress = (raw_progress - start_offset) % total_distance
        else:
            car.progress = 0
    
    finished_cars = [car for car in cars.values() if car.finished and car.final_position is not None]
    non_finished_cars = [car for car in cars.values() if not (car.finished and car.final_position is not None)]
    
    finished_cars.sort(key=lambda car: car.final_position)
    non_finished_cars.sort(key=lambda car: (car.lap_count, car.progress), reverse=True)
    
    sorted_cars = finished_cars + non_finished_cars
    
    for idx, car in enumerate(sorted_cars):
        car.position = idx + 1
    
    return sorted_cars