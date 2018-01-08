import math

from copy import deepcopy
from itertools import chain

from planet import Planet
from runner import get_get_new_positions

from tkinter import (
    Canvas, Button, Entry, Label, LabelFrame,
    BooleanVar, DoubleVar,
    W, N, E, S,
    ALL, DISABLED, NORMAL,
    TOP, BOTTOM, LEFT, RIGHT,
    INSERT,
)

from tkinter.ttk import Frame, Checkbutton


DELTA_T = 100000
ANIMATION_T = 10


def get_planet_configs(
    canvas_width,
    canvas_height,
    earth_true_anomaly,
    mars_true_anomaly,
    ship_true_anomaly,
):
    canvas_orbit_radius = min(canvas_height, canvas_width) / 2 - 30
    start_of_coordinates = (canvas_width / 2, canvas_height / 2)

    sun_config = dict(
        large_half_life=0,
        planet_r=30,  # pixels
        orbit_center=start_of_coordinates,
        eccentricity=0,
        color='yellow',
        lambda_initial=0,
        lambda_offset=0,
        mass=1.989 * math.pow(10, 30),
    )

    earth_config = dict(
        large_half_life=1.496 * math.pow(10, 11),  # meters
        planet_r=20,  # pixels
        orbit_center=start_of_coordinates,
        eccentricity=0.0167,
        color='blue',
        lambda_initial=0,
        lambda_offset=earth_true_anomaly,
        perihelion_longitude=336,
        mass=5.972 * math.pow(10, 24),
    )

    mars_config = dict(
        large_half_life=2.279 * math.pow(10, 11),  # meters
        planet_r=10,  # pixels
        orbit_center=start_of_coordinates,
        eccentricity=0.0934,
        color='red',
        lambda_initial=0,
        lambda_offset=mars_true_anomaly,
        perihelion_longitude=101,
        mass=6.39 * math.pow(10, 23),
    )

    ship_config = deepcopy(earth_config)
    ship_config.update(dict(
        color='green',
        lambda_offset=ship_true_anomaly,
        planet_r=5,
        mass=10000,
    ))

    scale = canvas_orbit_radius / max(
        earth_config['large_half_life'] * (1 + earth_config['eccentricity']),
        mars_config['large_half_life'] * (1 + mars_config['eccentricity']),
    )
    return dict(
        earth_config=earth_config,
        sun_config=sun_config,
        mars_config=mars_config,
        ship_config=ship_config,
        canvas_orbit_radius=canvas_orbit_radius,
        scale=scale,
    )


def chunkinate_iterable(iterable, size):
    while True:
        next_item = next(iterable)

        def query_chunk():
            yield next_item
            for i in range(size - 1):
                yield next(iterable)
        yield query_chunk()


class Panel(Frame):
    def __init__(self, canvas, root, **kwargs):
        super().__init__(root, **kwargs)
        self.canvas = canvas
        self.pack_propagate(0)
        self.with_ship = BooleanVar(self, value=True)

        self.runner = None
        self.planets = self.objects_with_custom_accelerations = ()
        self.earth = self.mars = self.ship = self.sun = None
        self.init_ui()

    def init_ui(self):
        exit_button = Button(self, text='Quit', command=self.quit, bg='#ffaaaa')
        exit_button.pack(side=BOTTOM)

        group = LabelFrame(self, text='True Anomaly settings')
        group.pack(side=TOP)

        fr1 = Frame(group)
        fr1.pack(side=TOP)
        self.earth_true_anomaly_label = Label(fr1, text='Earth True Anomaly')
        self.earth_true_anomaly_label.pack(side=LEFT)
        self.earth_true_anomaly_widget = Entry(fr1)
        self.earth_true_anomaly_widget.pack(side=RIGHT)
        self.earth_true_anomaly_widget.insert(INSERT, 259)

        fr2 = Frame(group)
        fr2.pack(side=TOP)
        self.mars_true_anomaly_label = Label(fr2, text='Mars True Anomaly')
        self.mars_true_anomaly_label.pack(side=LEFT)
        self.mars_true_anomaly_widget = Entry(fr2)
        self.mars_true_anomaly_widget.pack(side=RIGHT)
        self.mars_true_anomaly_widget.insert(INSERT, 260)

        fr3 = Frame(group)
        fr3.pack(side=TOP)
        self.ship_true_anomaly_label = Label(fr3, text='Earth True Anomaly')
        self.ship_true_anomaly_label.pack(side=LEFT)
        self.ship_true_anomaly_widget = Entry(fr3)
        self.ship_true_anomaly_widget.pack(side=RIGHT)
        self.ship_true_anomaly_widget.insert(INSERT, 244)

        with_ship_button = Checkbutton(
            self, text='With Ship',
            variable=self.with_ship,
            command=self.toggle_with_ship)
        with_ship_button.pack()

        start_button = Button(self, text='START', command=self.init_start_positions, bg='#aaddff')
        start_button.config(width=20, height=4)
        start_button.pack(side=TOP)

        self.stop_button = Button(self, text='STOP', command=self.stop_running, bg='#aaddff')
        self.stop_button.config(width=20, height=4)
        self.set_stop_button_state()
        self.stop_button.pack(side=TOP)

        self.resume_button = Button(self, text='RESUME', command=self.resume_running, bg='#aaddff')
        self.resume_button.config(width=20, height=4)
        self.set_resume_button_state()
        self.resume_button.pack(side=TOP)


    def init_start_positions(self):
        self.canvas.delete(ALL)
        if self.runner is not None:
            self.master.after_cancel(self.runner)

        configs = get_planet_configs(
            int(self.canvas['width']),
            int(self.canvas['height']),
            earth_true_anomaly=float(self.earth_true_anomaly_widget.get()),
            mars_true_anomaly=float(self.mars_true_anomaly_widget.get()),
            ship_true_anomaly=float(self.ship_true_anomaly_widget.get()),
        )
        scale = configs['scale']

        self.earth = Planet(self.canvas, scale, **configs['earth_config'])
        self.mars = Planet(self.canvas, scale, **configs['mars_config'])
        self.ship = Planet(self.canvas, scale, **configs['ship_config'])

        self.planets = (self.earth, self.mars)
        self.objects_with_custom_accelerations = (self.ship,) if self.with_ship.get() else ()

        self.sun = Planet(self.canvas, scale, **configs['sun_config'])
        self.resume_running()

    def run_system(self, sun, planets, objects_with_custom_accelerations):
        results = iter(get_get_new_positions(
            sun,
            planets=planets,
            delta_t=DELTA_T,
            objects_with_custom_accelerations=objects_with_custom_accelerations,
        ))
        for (x, v_x, y, v_y), p in zip(chunkinate_iterable(results, 4),
                                       chain(planets, objects_with_custom_accelerations)):
            p.move(x, y)
            p.left_trace_dot()
            p.set_coordinates_and_velocity(x, v_x, y, v_y)

        self.runner = self.master.after(
            ANIMATION_T,
            lambda: self.run_system(sun, planets, objects_with_custom_accelerations),
        )
        self.set_stop_button_state()

    def stop_running(self):
        self.set_resume_button_state()
        if self.runner is not None:
            self.master.after_cancel(self.runner)

    def resume_running(self):
        self.run_system(self.sun, self.planets, self.objects_with_custom_accelerations)

    def toggle_with_ship(self):
        print('With ship: %s' % self.with_ship.get())

    def set_resume_button_state(self):
        self.resume_button.configure(state=DISABLED if not self.sun else NORMAL)

    def set_stop_button_state(self):
        self.stop_button.configure(state=DISABLED if not self.runner else NORMAL)


class Gui:
    def __init__(self, root):
        self.root = root
        self.panel_width = 400
        self.root.geometry('%sx%s+0+0' % (self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        self.root.update()
        self.canvas_width = self.root.winfo_width() - self.panel_width
        self.canvas_height = self.root.winfo_height()
        self.canvas = Canvas(
            root,
            width=self.canvas_width,
            height=self.canvas_height,
            background='black',
        )
        self.canvas.grid(row=0, column=0, sticky=E+W+S+N)

        self.panel = Panel(self.canvas, root, width=self.panel_width, height=self.canvas_height, padding=10)
        self.panel.grid(row=0, column=1)
