# path_utils.py
import cv2
import numpy as np
from tracking_utils import project_to_centerline

def expand_path(path_points, width):
    # Bereidt het traject (path) voor door de coördinaten in een numpy-array te zetten.
    return np.array(path_points, dtype=np.int32)

def expand_path(path_points, width):
    """
    Breidt een gegeven centerline uit tot een volledige baan (track) met de opgegeven breedte.
    
    De functie werkt als volgt:
      1. Controleer of er minimaal twee punten in 'path_points' staan. Is dit niet zo,
         wordt een lege array geretourneerd.
      2. Zet de lijst van (x, y)-coördinaten om in een NumPy-array (float32): dit is handig
         voor rekenkundige bewerkingen.
      3. Bereken de vectoren tussen opeenvolgende punten met np.diff. Dit levert per segment 
         een vector op van het ene punt naar het volgende.
      4. Normaliseer deze vectoren zodat je voor elk segment een richtingsvector hebt. Door 
         de norm te berekenen voeg je een kleine constante (1e-6) toe om deling door nul te voorkomen.
      5. Bepaal de normale vector voor elk segment (de “linker normale” krijgt je door de vector 
         te roteren: (-dy, dx)). Deze normals wijzen naar de linkerkant van elk segment.
      6. Bepaal voor elk punt op de centerline een gemiddelde normaal. De eerste en laatste 
         punten hebben respectievelijk de normale van het eerste of laatste segment; in de 
         tussenzijde bereken je het gemiddelde van de normale vectoren van het vorige en het volgende segment en normaliseer deze.
      7. Bereken voor elk punt twee nieuwe punten:
         - offset_left: het originele punt naar links verschoven met half de baanbreedte (width/2)
         - offset_right: het originele punt naar rechts verschoven met hetzelfde bedrag.
      8. Vorm een gesloten polygon door de linker offsetpunten in de originele volgorde te 
         combineren met de rechter offsetpunten in omgekeerde volgorde.
      9. Converteer het resultaat naar een NumPy-array met type int32 (geschikt voor OpenCV-functies).
    
    Args:
        path_points (list of tuple): De lijst met (x, y)-coördinaten die de centerline van de baan vertegenwoordigen.
        width (float): De totale breedte van de baan.
    
    Returns:
        numpy.ndarray: Een array van punten (int32) die een gesloten polygon vormen, 
                       geschikt voor gebruik met OpenCV (bv. cv2.fillPoly of cv2.polylines).
    
    Let op:
        - Als er minder dan twee punten zijn, retourneert de functie een lege array.
    """
    
    # Controleer of er voldoende punten zijn
    if len(path_points) < 2:
        return np.array([], dtype=np.int32)
    
    # Stap 2: Converteer de lijst van punten naar een NumPy-array van dtype float32.
    path_points = np.array(path_points, dtype=np.float32)
    
    # Stap 3: Bereken de vector (verschil) tussen opeenvolgende punten.
    # Dit levert een array waarbij elke rij een vector is van punt i naar punt i+1.
    vectors = np.diff(path_points, axis=0)
    
    # Stap 4: Bereken de norm (lengte) van elke vector.
    # We voegen een kleine constante toe (1e-6) om te voorkomen dat we delen door 0.
    norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-6
    norm_vectors = vectors / norms  # Normaliseer elk vector zodat deze eenheid heeft
    
    # Stap 5: Bereken voor elk segment de normale vector.
    # De linker normale voor een vector (dx, dy) is (-dy, dx).
    normals = np.column_stack((-norm_vectors[:, 1], norm_vectors[:, 0]))
    
    half_width = width / 2.0

    # Stap 6: Voor elk punt op de centerline berekenen we een "gemiddelde" normale.
    # Dit helpt bij bochten waarbij de normale van opeenvolgende segmenten kan verschillen.
    offset_left = []
    offset_right = []
    for i in range(len(path_points)):
        if i == 0:
            # Het eerste punt: gebruik de normale van het eerste segment.
            normal = normals[0]
        elif i == len(path_points) - 1:
            # Het laatste punt: gebruik de normale van het laatste segment.
            normal = normals[-1]
        else:
            # Voor tussenliggende punten: neem het gemiddelde van de normale vectoren van
            # het vorige en het volgende segment.
            normal = (normals[i-1] + normals[i]) / 2.0
            n_norm = np.linalg.norm(normal)
            if n_norm > 0:
                normal = normal / n_norm  # Normaliseer
        # Stap 7: Bereken de linker en rechter offsetpunten.
        offset_left.append(path_points[i] + half_width * normal)
        offset_right.append(path_points[i] - half_width * normal)
    
    # Stap 8: Vorm een gesloten polygon.
    # Hiervoor combineer je de linker offsetpunten in originele volgorde met de rechter offsetpunten in omgekeerde volgorde.
    offset_right.reverse()
    expanded_polygon = np.vstack((offset_left, offset_right))
    
    # Stap 9: Converteer naar int32 voor compatibiliteit met OpenCV.
    return expanded_polygon.astype(np.int32)

def compute_cumulative_distances(path_points):
    #Bereken de cumulatieve afstanden langs het traject.
    cum_distances = [0.0]
    for i in range(1, len(path_points)):
        p1 = np.array(path_points[i - 1], dtype=float)
        p2 = np.array(path_points[i], dtype=float)
        distance = np.linalg.norm(p2 - p1)
        cum_distances.append(cum_distances[-1] + distance)
    return cum_distances

def calculate_progress_distance(car, path_points):
    """
    Berekent de afgelegde afstand (raw progress) langs het traject voor een auto,
    zijnde de cumulatieve afstand van het eerste punt tot aan het punt op het traject
    dat het dichtst bij de auto ligt. Hier werken we in het display-systeem door BLACK_BAR_WIDTH
    op te tellen bij de x-waarde.
    """

    # Debug: Controleer de huidige coördinaten van de auto
    print(f"DEBUG: Auto {car.marker_id} positie voor progressie: x={car.x}, y={car.y}")
    
    # Bereken de progressie langs het pad
    progress_distance = project_to_centerline((car.x, car.y), path_points)

    # Debug: Controleer de berekende progressie
    print(f"DEBUG: Auto {car.marker_id} berekende progressie: {progress_distance}")
    
    # Update de progressie van de auto
    car.progress = progress_distance
    
    if car.x is None or car.y is None:
        return 0.0
    # Verander raw x naar display x: voeg de offset toe.
    car_pos = np.array([car.x, car.y], dtype=float)
    cum_distances = compute_cumulative_distances(path_points)
    best_progress = 0.0
    min_perp = float('inf')
    for i in range(len(path_points) - 1):
        A = np.array(path_points[i], dtype=float)
        B = np.array(path_points[i+1], dtype=float)
        AB = B - A
        if np.dot(AB, AB) == 0:
            continue
        t = np.dot(car_pos - A, AB) / np.dot(AB, AB)
        t_clamped = np.clip(t, 0, 1)
        P = A + t_clamped * AB
        perp_distance = np.linalg.norm(car_pos - P)
        if perp_distance < min_perp:
            min_perp = perp_distance
            segment_length = np.linalg.norm(AB)
            progress = cum_distances[i] + t_clamped * segment_length
            best_progress = progress
    return best_progress
