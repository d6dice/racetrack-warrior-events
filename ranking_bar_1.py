# ranking_bar.py
import cv2
from utils_1 import overlay_image
from config_1 import FONT, FONT_SCALE_RANKING_BAR, THICKNESS, LINE_TYPE, COLOR_WHITE

def draw_ranking_bar(frame, cars, config):
    frame_with_ranking = frame.copy()
    ranking_bar_height = config['ranking_bar_height']
    positions = config['positions']
    max_positions = len(positions)

    # Teken de zwarte ranglijstbalk onderaan
    cv2.rectangle(
        frame_with_ranking,
        (0, frame_with_ranking.shape[0] - ranking_bar_height),
        (frame_with_ranking.shape[1], frame_with_ranking.shape[0]),
        (0, 0, 0), -1
    )

    # Sorteer de auto's op basis van rondetellingen en laatste rondetijden
    sorted_cars = sorted(
        cars,
        key=lambda x: (-x.lap_count, x.last_lap_time)
    )

    # Haal configuratieparameters op
    car_image_offset_x = config['car_image_offset_x']
    car_image_offset_y = config['car_image_offset_y']
    car_image_ranking_bar_offset_x = config.get('car_image_offset_ranking_bar_x', 0)
    text_offset_x = config.get('text_offset_x', 0)
    y_offset = config['y_offset']
    text_spacing = config['text_spacing']
    font = config['text_font']
    font_scale = FONT_SCALE_RANKING_BAR  # Gebruik de specifieke tekstgrootte voor de ranglijstbalk
    thickness = config['text_thickness']
    color = config['text_color']
    line_type = config['text_line_type']
    car_scale_multiplier = config['car_scale_multiplier']

    for i, car in enumerate(sorted_cars[:max_positions]):
        position_text = positions[i]

        text_size = cv2.getTextSize(
            position_text, font, font_scale, thickness
        )[0]
        x_text = (frame_with_ranking.shape[1] - text_size[0]) // 2 + text_offset_x
        y_text = frame_with_ranking.shape[0] - (y_offset - text_spacing * i)

        # Teken de positie-tekst
        cv2.putText(
            frame_with_ranking,
            position_text,
            (x_text, y_text),
            font, font_scale, color, thickness, line_type
        )

        if car.lap_count > 1:
            car_image = car.car_image
            car_scale_factor = car_scale_multiplier * (
                text_size[1] / car_image.shape[0]
            )

            car_width = int(car_image.shape[1] * car_scale_factor)
            car_height = int(car_image.shape[0] * car_scale_factor)
            car_image_resized = cv2.resize(
                car_image,
                (car_width, car_height),
                interpolation=cv2.INTER_AREA
            )

            x_car = x_text + text_size[0] + car_image_offset_x + car_image_ranking_bar_offset_x
            y_car = y_text - car_height // 2 + car_image_offset_y

            # Zorg ervoor dat de afbeelding binnen de ranglijstbalk blijft
            y_car = max(
                y_car,
                frame_with_ranking.shape[0] - ranking_bar_height
            )

            overlay_image(frame_with_ranking, car_image_resized, x_car, y_car)

    return frame_with_ranking
