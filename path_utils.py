#path_utils.py

import numpy as np

def expand_path(path_points, width):
    """
    Breidt het gegeven pad uit tot een baan met de opgegeven breedte.
    
    Gegeven een centerline (een lijst van (x, y)-coördinaten), berekent deze functie
    twee parallelle lijnen op een afstand van width/2 aan beide zijden van de centerline.
    De linker- en rechteroffsetpunten worden gecombineerd tot één gesloten polygon
    die de baan (het track-gebied) representeren.
    
    Args:
        path_points (list of tuple): Lijst met (x, y)-coördinaten die de centerline van de baan weergeven.
        width (float): Totale breedte van de baan.
    
    Returns:
        numpy.ndarray: Een array van punten (in int32) die een gesloten polygon vormt, geschikt voor
                       gebruik in OpenCV (bijv. met cv2.fillPoly of cv2.polylines).
    
    Let op:
        - Als er minder dan twee punten zijn, retourneert de functie een lege array.
    """
    if len(path_points) < 2:
        return np.array([], dtype=np.int32)
    
    # Zet de punten op in een NumPy-array
    path_points = np.array(path_points, dtype=np.float32)
    
    # Bereken vectoren tussen opeenvolgende punten
    vectors = np.diff(path_points, axis=0)
    
    # Normeer de vectoren (voorkom deling door nul)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-6
    norm_vectors = vectors / norms
    
    # Bereken de normale vectoren (voor elk segment: de linker normaal is (-dy, dx))
    normals = np.column_stack((-norm_vectors[:, 1], norm_vectors[:, 0]))
    
    half_width = width / 2.0

    # Voor elk punt berekenen we een gemiddelde normaal (bij buigingen)
    offset_left = []
    offset_right = []
    for i in range(len(path_points)):
        if i == 0:
            normal = normals[0]
        elif i == len(path_points) - 1:
            normal = normals[-1]
        else:
            # Gemiddelde van de normale vector van het vorige en volgende segment
            normal = (normals[i-1] + normals[i]) / 2.0
            norm = np.linalg.norm(normal)
            if norm > 0:
                normal = normal / norm
        offset_left.append(path_points[i] + half_width * normal)
        offset_right.append(path_points[i] - half_width * normal)
    
    # Vorm een gesloten polygon:
    # De linker offset in de originele volgorde en dan de rechter offset in omgekeerde volgorde.
    offset_right.reverse()
    expanded_polygon = np.vstack((offset_left, offset_right))
    
    return expanded_polygon.astype(np.int32)