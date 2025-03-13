import math
import numpy as np

def distance_between_points(p1, p2):
    """
    Bereken de Euclidische afstand tussen twee punten.
    """
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def project_point_to_segment(point, seg_start, seg_end):
    """
    Projecteer een punt op een lijnsegment en geef terug hoeveel afstand (langzaam)
    langs het segment is bereikt en wat de loodrechte afstand is.

    Parameters:
        point: (x, y) van het punt dat geprojecteerd wordt.
        seg_start, seg_end: (x, y) punten die het segment definiëren.

    Returns:
        proj_distance: afstand langs het segment van het startpunt tot aan de projectie.
        perp_distance: loodrechte afstand van het punt tot aan de projectie op het segment.
    """
    p = np.array(point, dtype=float)
    a = np.array(seg_start, dtype=float)
    b = np.array(seg_end, dtype=float)
    
    ab = b - a
    ap = p - a
    ab_norm_sq = np.dot(ab, ab)
    if ab_norm_sq == 0:
        # Degeneraat segment
        return 0, distance_between_points(point, seg_start)
    t = np.dot(ap, ab) / ab_norm_sq
    # Zorg dat t tussen 0 en 1 ligt (binnen het segment)
    t = max(0, min(1, t))
    projection = a + t * ab
    proj_distance = np.linalg.norm(projection - a)
    perp_distance = np.linalg.norm(p - projection)
    return proj_distance, perp_distance

def project_to_centerline(point, centerline):
    """
    Berekent hoe ver (in pixels of andere eenheid) een meegegeven point 
    al is langs de opgegeven centerline (de "middenlijn" van de baan).

    Parameters:
        point: (x, y) positie van de auto in het camerabeeld.
        centerline: Een lijst van punten [(x1, y1), (x2, y2), ...] die de middellijn van de baan definiëren.
    
    Returns:
        best_progress: Een getal dat de totale afgelegde afstand langs de centerline aangeeft tot het
                       punt dat het dichtst bij 'point' ligt.
    """
    total_length = 0
    best_progress = 0
    min_perp_distance = float('inf')
    
    # Loop door alle segmenten van de centerline
    for i in range(len(centerline) - 1):
        seg_start = centerline[i]
        seg_end = centerline[i+1]
        proj_distance, perp_distance = project_point_to_segment(point, seg_start, seg_end)
        # Houd bij welk segment de kleinste loodrechte afstand heeft
        if perp_distance < min_perp_distance:
            min_perp_distance = perp_distance
            best_progress = total_length + proj_distance
        total_length += distance_between_points(seg_start, seg_end)
        
    return best_progress
