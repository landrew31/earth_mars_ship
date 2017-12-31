import math
import tkinter as tk


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
        self, canvas, scale,
        large_half_life=0,
        planet_r=0,
        orbit_center=(0, 0),
        eccentricity=0,
        color='red',
        lambda_initial=0,
        lambda_offset=0,
        perihelion_longitude=0,
    ):
        self.canvas = canvas
        self.scale = scale
        self.color = color

        self.large_half_life = large_half_life
        self.orbit_eccentricity = eccentricity
        self.perihelion_longitude = to_radian(perihelion_longitude)
        self._equinox_dot_initial_angle = math.pi / 2
        self.planet_r = planet_r
        self.perihelion_velocity = self.__get_perihelion_velocity()
        self.perihelion_radius = self.large_half_life * (1 - self.orbit_eccentricity)
        self.orbit_x = orbit_center[0]
        self.orbit_y = orbit_center[1]
        # print(self.orbit_x, self.orbit_y)
        self._lambda = to_radian(lambda_initial + lambda_offset)

        self.orbit_r = self.__get_current_orbit_radius()
        self.current_velocity = self.__get_current_velocity()
        # print(self.current_velocity)
        self.angular_velocity = self.__get_current_angular_velocity()
        # self.x, self.y = self.turn_orbit_to_appropriate_perihelion_longitude(
        #     self.__get_next_x_coordinate(),
        #     self.__get_next_y_coordinate(),
        # )
        x, y = self.__get_next_coordinates()
        self.x = x
        self.y = y
        # print(self.x, self.y, self.orbit_r)
        # print(scale * self.x, scale * self.y)

        self.item = canvas.create_oval(
            scale * self.x - planet_r, scale * self.y - planet_r,
            scale * self.x + planet_r, scale * self.y + planet_r,
            fill=color,
        )
        self.print_orbit_skeleton()

    def print_orbit_skeleton(self):
        c_width = int(self.canvas.cget('width'))
        c_height = int(self.canvas.cget('height'))
        zero_x = c_width / 2
        zero_y = c_height / 2
        vertical_line = (
            - zero_x + PLANET_ORBIT_LINES_PADDING, 0,
            c_width - PLANET_ORBIT_LINES_PADDING, 0,
        )
        # vertical_line = (
        #     PLANET_ORBIT_LINES_PADDING, zero_y,
        #     c_width - PLANET_ORBIT_LINES_PADDING, zero_y,
        # )

        print(vertical_line)

        long_semi_axis_angle = self.perihelion_longitude + self._equinox_dot_initial_angle
        long_x = turn_dot_on_angle(*vertical_line[:2], long_semi_axis_angle)
        long_y = turn_dot_on_angle(*vertical_line[2:], long_semi_axis_angle)
        print(long_x, long_y)

        short_semi_axis_angle = self.perihelion_longitude + self._equinox_dot_initial_angle + math.pi

        # self.canvas.create_line(
        #     self.orbit_x / self.scale + long_x[0], self.orbit_x / self.scale + long_x[1],
        #     self.orbit_y / self.scale + long_x[0], self.orbit_x / self.scale + long_y[1],
        #     fill=self.color,
        #     dash=(5, 5),
        # )
        self.canvas.create_line(
            *long_x, *long_y,
            fill=self.color,
            dash=(5, 5),
        )
        self.canvas.create_line(
            *vertical_line,
            fill=self.color,
            dash=(5, 5),
        )
        # self.canvas.create_line(
        #     *turn_dot_on_angle(*vertical_line[:2], short_semi_axis_angle),
        #     *turn_dot_on_angle(*vertical_line[2:], short_semi_axis_angle),
        #     fill=self.color,
        #     dash=(5, 5),
        # )

    def move(self, delta_x, delta_y):
        print(self.scale * delta_x, self.scale * delta_y)
        self.canvas.move(self.item, self.scale * delta_x, self.scale * delta_y)

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

    def __get_current_angular_velocity(self):
        return self.perihelion_velocity * self.perihelion_radius / (self.orbit_r ** 2) if self.orbit_r else 0

    def __get_current_velocity(self):
        velocity = math.sqrt(G * SUN_MASS / self.orbit_r) if self.orbit_r else 0
        self.v_x = velocity * math.sin(self._lambda)
        self.v_y = velocity * math.cos(self._lambda)
        return velocity

    def __get_next_x_coordinate(self):
        return self.orbit_x / self.scale + self.orbit_r * math.sin(self._lambda)

    def __get_next_y_coordinate(self):
        return self.orbit_y / self.scale + self.orbit_r * math.cos(self._lambda)

    def __get_next_coordinates(self):
        x, y = self.turn_orbit_to_appropriate_perihelion_longitude(
            self.orbit_r * math.sin(self._lambda),
            self.orbit_r * math.cos(self._lambda),
        )
        next_x = self.orbit_x / self.scale + x
        next_y = self.orbit_y / self.scale + y
        return next_x, next_y
        # return (
        #     next_x * math.cos(self.perihelion_longitude) + next_y * math.sin(self.perihelion_longitude),
        #     next_y * math.cos(self.perihelion_longitude) + next_x * math.sin(self.perihelion_longitude),
        # )

    def calculate_next(self, delta_t):
        self.angular_velocity = self.__get_current_angular_velocity()
        self._lambda += self.angular_velocity * delta_t
        self.orbit_r = self.__get_current_orbit_radius()
        next_x, next_y = self.__get_next_coordinates()
        # next_x, next_y = self.turn_orbit_to_appropriate_perihelion_longitude(
        #     self.__get_next_x_coordinate(),
        #     self.__get_next_y_coordinate()
        # )
        # print(
        #     (next_x - self.x),
        #     (next_y - self.y),
        # )
        self.move(
            (next_x - self.x),
            (next_y - self.y),
        )
        self.x, self.y = next_x, next_y

    def turn_orbit_to_appropriate_perihelion_longitude(self, x, y):
        turn_over_angle = self.perihelion_longitude + self._equinox_dot_initial_angle
        return turn_dot_on_angle(x, y, turn_over_angle)

    def left_trace_dot(self):
        self.canvas.create_oval(
            int(self.scale * self.x), int(self.scale * self.y),
            int(self.scale * self.x) + 1, int(self.scale * self.y) + 1,
        )
