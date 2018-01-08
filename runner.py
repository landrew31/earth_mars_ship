import math

from functools import reduce
from itertools import chain


from runge_kutta_solver import solve_runge_kutta


G = 6.674 * math.pow(10, -11)
A = 0.0007


def acceleration_y(central_body, moving):
    return (
        G * central_body.mass * (central_body.y - moving.y)
        / math.pow(
            (central_body.x - moving.x) ** 2
            + (central_body.y - moving.y) ** 2,
            3 / 2,
        )
    )


def acceleration_x(central_body, moving):
    return (
        G * central_body.mass * (central_body.x - moving.x)
        / math.pow(
            (central_body.x - moving.x) ** 2
            + (central_body.y - moving.y) ** 2,
            3 / 2,
        )
    )


def get_new_position_around_sun(planet, sun, delta_t):
    earth_vx = planet.v_x + acceleration_x(sun, planet) * delta_t
    earth_vy = planet.v_y + acceleration_y(sun, planet) * delta_t
    earth_x = planet.x + earth_vx * delta_t
    earth_y = planet.y + earth_vy * delta_t
    return earth_x, earth_y, earth_vx, earth_vy


def get_get_new_positions(sun, planets, delta_t, objects_with_custom_accelerations=()):
    functions = get_functions(sun, planets, objects_with_custom_accelerations)
    current_positions_and_velocities = []
    for body in chain(planets, objects_with_custom_accelerations):
        current_positions_and_velocities.extend([body.x, body.v_x, body.y, body.v_y])
    return solve_runge_kutta(functions, current_positions_and_velocities, delta_t)


def get_functions(sun, planets, objects_with_custom_accelerations):
    functions = []
    num_of_moving = len(planets) + len(objects_with_custom_accelerations)
    for i, body in enumerate(chain(planets, objects_with_custom_accelerations)):

        def get_acceleration_for_body(y_x, y_y):
            a = [
                (
                    b.get_acceleration_pair(math.sqrt((y_x - b.x) ** 2 + (y_y - b.y) ** 2)),
                    i_b,
                ) for i_b, b in enumerate(chain(planets, objects_with_custom_accelerations, [sun]))
                ]
            ad = list(filter(lambda t: t[0] and t[0][0] and t[0][1], a))
            a_pairs = sorted(ad, key=lambda t: t[0][0])
            print(a_pairs)
            if a_pairs:
                (d, a), central_body_index = a_pairs[0]
                return a, central_body_index
            return 0, 0

        def get_current_object_equations(i=i, body=body):
            a, accelerate_to = get_acceleration_for_body(body.x, body.y) if body in objects_with_custom_accelerations else (0, 0)
            print(a, accelerate_to, body in objects_with_custom_accelerations)
            return [
                lambda *y: y[i * 4 + 1],
                lambda *y: reduce(lambda acc, v: acc + v, chain(
                    [
                        -get_g_x(sun.mass, y[i * 4], y[i * 4 + 2]),
                    ],
                    [
                        -get_g_x(body.mass, y[i * 4] - y[i_b * 4], y[i * 4 + 2] - y[i_b * 4 + 2]) if b != body else 0
                        for i_b, b in enumerate(chain(planets, objects_with_custom_accelerations))
                    ],
                    (
                        [-get_a_x(
                            a,
                            y[i * 4] - (y[accelerate_to * 4] if accelerate_to < num_of_moving else 0),
                            y[i * 4 + 2] - (y[accelerate_to * 4 + 2] if accelerate_to < num_of_moving else 0)
                        )]
                        if body in objects_with_custom_accelerations and a else []
                    ),
                ), 0),
                lambda *y: y[i * 4 + 3],
                lambda *y: reduce(lambda acc, v: acc + v, chain(
                    [-get_g_y(sun.mass, y[i * 4], y[i * 4 + 2])],
                    [
                        -get_g_y(body.mass, y[i * 4] - y[i_b * 4], y[i * 4 + 2] - y[i_b * 4 + 2]) if b != body else 0
                        for i_b, b in enumerate(chain(planets, objects_with_custom_accelerations))
                    ],
                    (
                        [-get_a_y(
                            a,
                            y[i * 4] - (y[accelerate_to * 4] if accelerate_to < num_of_moving else 0),
                            y[i * 4 + 2] - (y[accelerate_to * 4 + 2] if accelerate_to < num_of_moving else 0)
                        )]
                        if body in objects_with_custom_accelerations and a else []
                    ),
                ), 0),
            ]

        functions.extend(get_current_object_equations())
    return functions


def __get_pref(mass, distance_x, distance_y):
    return G * mass / math.pow((distance_x ** 2 + distance_y ** 2), 3 / 2)


def get_g_x(mass, distance_x, distance_y):
    return distance_x * __get_pref(mass, distance_x, distance_y)


def get_g_y(mass, distance_x, distance_y):
    return distance_y * __get_pref(mass, distance_x, distance_y)


def get_a_x(a, distance_x, distance_y):
    return a * distance_x / math.pow((distance_x ** 2 + distance_y ** 2), 1 / 2)


def get_a_y(a, distance_x, distance_y):
    return a * distance_y / math.pow((distance_x ** 2 + distance_y ** 2), 1 / 2)
