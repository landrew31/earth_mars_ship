import math
import tkinter as tk

from planet import Planet


CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 1000
LINE_TO_POINT_OF_EQUINOX_PADDING = 50
TEXT_TO_POINT_OF_EQUINOX_MARGIN_TOP = 20
TEXT_TO_POINT_OF_EQUINOX_MARGIN_LEFT = 100
CANVAS_ORBIT_RADIUS = 450

ZERO_X = CANVAS_WIDTH / 2
ZERO_Y = CANVAS_HEIGHT / 2
START_OF_COORDINATES = (ZERO_X, ZERO_Y)


# Sun configs
SUN_RADIUS = 30  # pixels
SUN_ANG_VELOCITY = 0
SUN_ORBIT_RADIUS = 0
SUN_ORBIT_CENTER = START_OF_COORDINATES

sun_config = dict(
    large_half_life=0,
    planet_r=30,  # pixels
    orbit_center=START_OF_COORDINATES,
    eccentricity=0,
    color='yellow',
    lambda_initial=0,
    lambda_offset=0,
)


earth_config = dict(
    large_half_life=1.496 * math.pow(10, 11),  # meters
    planet_r=20,  # pixels
    orbit_center=START_OF_COORDINATES,
    eccentricity=0.0167,
    color='blue',
    lambda_initial=0,
    lambda_offset=259,
    perihelion_longitude=336,
    # perihelion_longitude=90,
)


mars_config = dict(
    large_half_life=2.279 * math.pow(10, 11),  # meters
    planet_r=10,  # pixels
    orbit_center=START_OF_COORDINATES,
    eccentricity=0.0934,
    color='red',
    lambda_initial=0,
    lambda_offset=24,
    perihelion_longitude=101,
    # perihelion_longitude=90,
)


DELTA_T = 100000
ANIMATION_T = 1


def run_system(root, earth, mars=None, sun=None):
    earth.calculate_next(DELTA_T)
    mars.calculate_next(DELTA_T)
    earth.left_trace_dot()
    mars.left_trace_dot()
    root.after(ANIMATION_T, lambda: run_system(root, earth, mars, sun))


def init_start_positions(root, canvas):
    scale = CANVAS_ORBIT_RADIUS / max(
        mars_config['large_half_life'] * (1 + mars_config['eccentricity']),
        earth_config['large_half_life'] * (1 + earth_config['eccentricity']),
    )
    canvas.create_line(
        LINE_TO_POINT_OF_EQUINOX_PADDING, ZERO_Y,
        CANVAS_WIDTH - LINE_TO_POINT_OF_EQUINOX_PADDING, ZERO_Y,
        arrow=tk.LAST,
        dash=(5, 5),
    )
    canvas.create_text(
        CANVAS_WIDTH - LINE_TO_POINT_OF_EQUINOX_PADDING, ZERO_Y,
        text='To the point\n\nof equinox',
    )
    earth = Planet(canvas, scale, **earth_config)
    mars = Planet(canvas, scale, **mars_config)
    sun = Planet(canvas, scale, **sun_config)
    run_system(root, earth, mars, sun)
