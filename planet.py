import math
from collections import namedtuple
from runner import get_new_position_around_sun

PLANET_ORBIT_LINES_PADDING = 100

SUN_MASS = 1.989 * math.pow(10, 30)
G = 6.674 * math.pow(10, -11)


def circle(canvas, x, y, r):
    return canvas.create_oval(x - r, y - r, x + r, y + r)


def to_radian(alfa):
    return (alfa * math.pi / 180) % (2 * math.pi)


def turn_dot_on_angle(x, y, turn_over_angle):
    return (
        x * math.cos(turn_over_angle) + y * math.sin(turn_over_angle),
        - x * math.sin(turn_over_angle) + y * math.cos(turn_over_angle),
    )


class Planet:
    def __init__(
        self, name, canvas, scale,
        large_half_life=0,
        planet_r=0,
        orbit_center=(0, 0),
        eccentricity=0,
        color='red',
        lambda_offset=0,
        perihelion_longitude=0,
        mass=None,
        a_config=(),
    ):
        self.name = name
        self.canvas = canvas
        self.scale = scale
        self.color = color
        self.mass = mass
        self.a_config = list(sorted(a_config, key=lambda t: t[0]))

        self.large_half_life = large_half_life
        self.orbit_eccentricity = eccentricity

        self.perihelion_longitude = to_radian(perihelion_longitude)
        self._equinox_dot_initial_angle = math.pi / 2
        self.init_lambda = self.perihelion_longitude + self._equinox_dot_initial_angle

        self.planet_r = planet_r

        self.perihelion_velocity = self.__get_perihelion_velocity()
        self.perihelion_radius = self.large_half_life * (1 - self.orbit_eccentricity)

        self.orbit_x = orbit_center[0]
        self.orbit_y = orbit_center[1]

        self._lambda = 0

        s = self.orbit_r = self.__get_current_orbit_radius()

        self.current_velocity = self.__get_current_velocity()
        self.x, self.y = self.__get_next_coordinates()

        self.__fit_velocity_and_position(to_radian(lambda_offset))

        self.x, self.y = self.turn_orbit_to_appropriate_perihelion_longitude(self.x, self.y)
        self.v_x, self.v_y = self.turn_orbit_to_appropriate_perihelion_longitude(self.v_x, self.v_y)
        a = self.orbit_r = math.sqrt(self.x ** 2 + self.y ** 2)

        rel_x, rel_y = self.get_relative_coordinates(self.x, self.y)
        self.rel_x, self.rel_y = rel_x, rel_y

        self.item = canvas.create_oval(
            scale * self.rel_x - planet_r, scale * self.rel_y - planet_r,
            scale * self.rel_x + planet_r, scale * self.rel_y + planet_r,
            fill=color,
        )

    def get_acceleration_pair(self, distance):
        for d, a in self.a_config:
            if d >= distance:
                return d, a

    def __get_current_angular_velocity(self):
        return self.perihelion_velocity * self.perihelion_radius / (self.orbit_r ** 2) if self.orbit_r else 0

    def move(self, new_x, new_y):
        new_rel_x, new_rel_y = self.get_relative_coordinates(new_x, new_y)
        delta_x = new_rel_x - self.rel_x
        delta_y = new_rel_y - self.rel_y
        self.canvas.move(self.item, self.scale * delta_x, self.scale * delta_y)
        self.rel_x = new_rel_x
        self.rel_y = new_rel_y

    def __get_next_coordinates(self):
        return (
            self.orbit_r * math.sin(self._lambda),
            self.orbit_r * math.cos(self._lambda),
        )

    def get_relative_coordinates(self, x, y):
        rel_x = self.orbit_x / self.scale + x
        rel_y = self.orbit_y / self.scale + y
        return rel_x, rel_y

    def set_coordinates_and_velocity(self, x, v_x, y, v_y):
        self.x = x
        self.v_x = v_x
        self.y = y
        self.v_y = v_y

    def turn_orbit_to_appropriate_perihelion_longitude(self, x, y):
        turn_over_angle = self.perihelion_longitude + self._equinox_dot_initial_angle
        return turn_dot_on_angle(x, y, turn_over_angle)

    def left_trace_dot(self):
        self.canvas.create_oval(
            int(self.scale * self.rel_x), int(self.scale * self.rel_y),
            int(self.scale * self.rel_x) + 1, int(self.scale * self.rel_y) + 1,
            outline=self.color,
            fill='white',
        )

    def __get_perihelion_velocity(self):
        return math.sqrt((
            (G * SUN_MASS * (1 + self.orbit_eccentricity))
            /
            (self.large_half_life * (1 - self.orbit_eccentricity))
        )) if self.large_half_life and self.orbit_eccentricity != 1 else 0

    def __get_current_orbit_radius(self):
        return (
            (self.large_half_life * (1 - math.pow(self.orbit_eccentricity, 2)))
            /
            (1 + self.orbit_eccentricity * math.cos(self._lambda))
        )

    def __get_current_velocity(self):
        velocity = math.sqrt(G * SUN_MASS * (2 / self.orbit_r - 1 / self.large_half_life)) if self.orbit_r else 0
        self.v_x = velocity * math.cos(self._lambda)
        self.v_y = velocity * math.sin(self._lambda)
        return velocity

    def __fit_velocity_and_position(self, _lambda):
        delta_t_to_fit = 10000
        SunPseudo = namedtuple('SunPseudo', ['x', 'y', 'mass'])
        mock_sun = SunPseudo(0, 0, SUN_MASS)
        while self._lambda < _lambda:
            self.x, self.y, self.v_x, self.v_y = get_new_position_around_sun(self, mock_sun, delta_t_to_fit)
            self.orbit_r = math.sqrt(self.x ** 2 + self.y ** 2)
            self._lambda += self.__get_current_angular_velocity() * delta_t_to_fit
