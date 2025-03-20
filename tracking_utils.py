import math
import numpy as np

def distance_between_points(p1, p2):
    """
    Bereken de Euclidische afstand tussen twee punten.

    Parameters:
        p1 (tuple): Het eerste punt als (x, y).
        p2 (tuple): Het tweede punt als (x, y).

    Returns:
        float: De afstand tussen p1 en p2.
    """
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def project_point_to_segment(point, seg_start, seg_end):
    """
    Projecteer een gegeven punt op een lijnsegment en retourneer:
       - De afstand langs het segment (van het startpunt seg_start tot het projectiepunt).
       - De loodrechte afstand (de minimale afstand) van het punt tot het segment.
    
    De procedure is als volgt:
      1. Zet de invoerpunten om naar NumPy-arrays (als floats) zodat rekenkundige operaties mogelijk zijn.
      2. Bereken de vector van het segment: AB = seg_end - seg_start.
      3. Bereken de vector van het startpunt van het segment naar het punt (AP = point - seg_start).
      4. Bereken de geprojecteerde factor t als de dot-product (AP dot AB) gedeeld door (AB dot AB).  
         Deze factor geeft aan hoe ver langs het segment de projectie ligt.
      5. Clamp t zodat het in het interval [0, 1] valt, zodat de projectie binnen het segment blijft.
      6. Bereken het projectiepunt P = seg_start + t * AB.
      7. De afstand langs het segment (proj_distance) is de afstand van seg_start naar P.
      8. De loodrechte afstand (perp_distance) is de afstand van het punt tot P.

    Parameters:
         point (tuple): Het punt dat geprojecteerd moet worden, als (x, y).
         seg_start (tuple): Beginnend punt van het segment.
         seg_end (tuple): Eindpunt van het segment.

    Returns:
         proj_distance (float): De afstand langs het segment vanaf seg_start tot P.
         perp_distance (float): De loodrechte afstand van het punt tot P.
    """
    # Zet de punten om naar float arrays voor nauwkeurige berekening
    p = np.array(point, dtype=float)
    a = np.array(seg_start, dtype=float)
    b = np.array(seg_end, dtype=float)
    
    ab = b - a
    ap = p - a
    ab_norm_sq = np.dot(ab, ab)
    
    if ab_norm_sq == 0:
        # Als het segment degenereert (start en eind zijn gelijk),
        # dan is de projectie niet definitief; gebruik dan de afstand van het punt tot seg_start.
        return 0, distance_between_points(point, seg_start)
    
    # Bereken de projectiefactor t
    t = np.dot(ap, ab) / ab_norm_sq
    # Clamp t zodat het waarde tussen 0 en 1 ligt (projectie ligt binnen het segment)
    t = max(0, min(1, t))
    
    # Bepaal het projectiepunt op het segment
    projection = a + t * ab
    # Afstand langs het segment (van seg_start naar de projectie)
    proj_distance = np.linalg.norm(projection - a)
    # Loodrechte afstand van het punt tot het projectiepunt
    perp_distance = np.linalg.norm(p - projection)
    
    return proj_distance, perp_distance


def project_to_centerline(point, centerline):
    """
    Berekent de progressie (afgelegde afstand) langs een centerline voor een gegeven punt.
    Dit betekent: we bepalen hoe ver langs de centerline (de "middenlijn" van de baan) het punt ligt.
    
    De methode werkt als volgt:
      1. Begin met een totaal lengte counter (total_length) gelijk aan 0.
      2. Voor elk segment in de centerline:
         - Projecteer 'point' op het segment (gebruik makend van project_point_to_segment).
         - Als de loodrechte afstand (perp_distance) kleiner is dan de
           huidige minimale gevonden afstand, onthoud dan de progress als:
              best_progress = total_length + proj_distance.
         - Tel de lengte van dit segment op bij total_length.
      3. Geef de best gevonden progress-waarde (best_progress) terug.

    Parameters:
         point (tuple): Het punt (zoals de positie van een auto) in (x, y) die je wilt projecteren.
         centerline (list of tuple): Een lijst van (x, y)-punten die de centerline van de baan definiëren.

    Returns:
         best_progress (float): De totale afgelegde afstand langs de centerline tot het punt dat 
                                het dichtst bij 'point' ligt.
    """
    total_length = 0
    best_progress = 0
    min_perp_distance = float('inf')
    
    # Loop over elk segment in de centerline (elk paar opeenvolgende punten)
    for i in range(len(centerline) - 1):
        seg_start = centerline[i]
        seg_end = centerline[i+1]
        
        # Projecteer het punt op dit segment
        proj_distance, perp_distance = project_point_to_segment(point, seg_start, seg_end)
        
        # Als dit segment een kleinere loodrechte afstand heeft, onthoud dan de progress
        if perp_distance < min_perp_distance:
            min_perp_distance = perp_distance
            best_progress = total_length + proj_distance
        
        # Tel de lengte van dit segment op bij de totale lengte
        total_length += distance_between_points(seg_start, seg_end)
        
    return best_progress

def process_detected_markers(new_frame, cars, parameters, aruco_dict, race_manager):
    """
    Detecteert ArUco-markers in new_frame en verwerkt ze.
    """
    gray = cv2.cvtColor(new_frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    # Debug: Bekijk de gedetecteerde ArUco-corners en IDs
    print(f"Detected ArUco corners: {corners}")
    print(f"Detected ArUco IDs: {ids}")
    
    if ids is not None and len(ids) > 0:
        process_markers(cars, corners, ids, new_frame, race_manager)

