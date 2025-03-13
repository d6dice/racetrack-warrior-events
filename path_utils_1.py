# path_utils.py

import numpy as np

def expand_path(path_points, width=20):
    expanded_points = []
    for i in range(len(path_points) - 1):
        p1, p2 = path_points[i], path_points[i + 1]
        # Bereken de vector van p1 naar p2
        vector = np.array(p2) - np.array(p1)
        norm = np.linalg.norm(vector)
        unit_vector = vector / norm if norm > 0 else np.array([0, 0])
        # Draai de vector 90 graden om een perpendiculaire richting te krijgen
        perpendicular = np.array([-unit_vector[1], unit_vector[0]])
        # Verschuif de punten langs de perpendiculaire richting om een breder pad te creëren
        p1_left = tuple((np.array(p1) + perpendicular * width / 2).astype(int))
        p1_right = tuple((np.array(p1) - perpendicular * width / 2).astype(int))
        p2_left = tuple((np.array(p2) + perpendicular * width / 2).astype(int))
        p2_right = tuple((np.array(p2) - perpendicular * width / 2).astype(int))
        expanded_points.append([p1_left, p2_left, p2_right, p1_right])
    return expanded_points
