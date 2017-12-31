import math
from copy import deepcopy
from scipy.integrate import ode

from planet import Planet, G, SUN_MASS

A = 1

CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 1000
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
)

ship_config = deepcopy(earth_config)
ship_config.update(dict(
    # large_half_life=1.496 * math.pow(10, 11),  # meters
    color='green',
    lambda_offset=24,
    planet_r=5,
))

DELTA_T = 100000
ANIMATION_T = 1


def run_system(root, earth, mars=None, sun=None, ship=None, *args, **kwargs):
    earth.calculate_next(DELTA_T)
    mars.calculate_next(DELTA_T)
    earth.left_trace_dot()
    mars.left_trace_dot()
    ship_x, ship_v_x, ship_y, ship_v_y = s(earth, mars, ship)
    ship.move(ship_x - ship.x, ship_y - ship.y)
    ship.left_trace_dot()
    ship.x = ship_x
    ship.y = ship_y
    ship.v_x = ship_v_x
    ship.v_y = ship_v_y
    root.after(ANIMATION_T, lambda: run_system(root, earth, mars, sun, ship))


def init_start_positions(root, canvas):
    scale = CANVAS_ORBIT_RADIUS / max(
        mars_config['large_half_life'],
        earth_config['large_half_life'],
    )
    earth = Planet(canvas, scale, **earth_config)
    mars = Planet(canvas, scale, **mars_config)
    sun = Planet(canvas, scale, **sun_config)
    ship = Planet(canvas, scale, **ship_config)
    run_system(root, earth, mars, sun, ship)


def __get_pref(distance_x, distance_y):
    return G * SUN_MASS / math.pow((distance_x ** 2 + distance_y ** 2), 3 / 2)


def get_g_x(distance_x, distance_y):
    # print(distance_x, distance_y)
    return distance_x * __get_pref(distance_x, distance_y)


def get_g_y(distance_x, distance_y):
    return distance_y * __get_pref(distance_x, distance_y)


def get_a_x(distance_x, distance_y):
    return A * distance_x * math.pow((distance_x ** 2 + distance_y ** 2), 1 / 2)


def get_a_y(distance_x, distance_y):
    return A * distance_y * math.pow((distance_x ** 2 + distance_y ** 2), 1 / 2)


def get_solver(*args):
    # print(args)
    x_earth, x_mars, y_earth, y_mars = args

    def solver(t, Y):
        # print(t)
        print(Y)
        return [
            Y[1],
            (
                get_g_x(Y[0] - x_earth, Y[2] - y_earth)
                - get_g_x(Y[0] - x_mars, Y[2] - y_mars)
                - get_g_x(Y[0], Y[2])
                + get_a_x(Y[0] - x_mars, Y[2] - y_mars)
            ),
            Y[3],
            (
                get_g_y(Y[0] - x_earth, Y[2] - y_earth)
                - get_g_y(Y[0] - x_mars, Y[2] - y_mars)
                - get_g_y(Y[0], Y[2])
                + get_a_y(Y[0] - x_mars, Y[2] - y_mars)
            ),
        ]
    return solver


def s(earth, mars, ship):
    t = 0
    x0 = [ship.x, ship.v_x, ship.y, ship.v_y]
    solve = get_solver(earth.x, mars.x, earth.y, mars.y)
    r = ode(solve).set_integrator('dopri5', nsteps=1)
    r.set_initial_value(x0, t)
    res = r.integrate(DELTA_T)
    print(11, res)
    return res
