import math

import os.path

from copy import deepcopy
from itertools import chain

from planet import Planet
from runner import get_get_new_positions

from tkinter import (
    Canvas, Button, Entry, Label, LabelFrame, Text,
    BooleanVar, DoubleVar,
    W, N, E, S,
    ALL, DISABLED, NORMAL, BOTH, END,
    TOP, BOTTOM, LEFT, RIGHT,
    INSERT,
)

from tkinter.ttk import Frame, Checkbutton


DELTA_T = 100000
START_VELOCITY = 30000
ANIMATION_T = 10
RESULT_DIRECTORY = 'results'
FILE_NAME_PREFIX = 'log_file'


def get_planet_configs(
    canvas_width,
    canvas_height,
    ship_start_velocity,
    earth_true_anomaly,
    mars_true_anomaly,
    ship_true_anomaly,
    ship_earth_a_config=(),
    ship_mars_a_config=(),
    ship_sun_a_config=(),
):
    canvas_orbit_radius = min(canvas_height, canvas_width) / 2 - 30
    start_of_coordinates = (canvas_width / 2, canvas_height / 2)

    sun_config = dict(
        large_half_life=0,
        planet_r=15,  # pixels
        orbit_center=start_of_coordinates,
        eccentricity=0,
        color='yellow',
        lambda_offset=0,
        mass=1.989 * math.pow(10, 30),
        a_config=ship_sun_a_config,
    )

    earth_config = dict(
        large_half_life=1.496 * math.pow(10, 11),  # meters
        planet_r=7,  # pixels
        orbit_center=start_of_coordinates,
        eccentricity=0.0167,
        color='blue',
        lambda_offset=earth_true_anomaly,
        perihelion_longitude=336,
        mass=5.972 * math.pow(10, 24),
        a_config=ship_earth_a_config,
    )

    mars_config = dict(
        large_half_life=2.279 * math.pow(10, 11),  # meters
        planet_r=4,  # pixels
        orbit_center=start_of_coordinates,
        eccentricity=0.0934,
        color='red',
        lambda_offset=mars_true_anomaly,
        perihelion_longitude=101,
        mass=6.39 * math.pow(10, 23),
        a_config=ship_mars_a_config,
    )

    ship_config = deepcopy(earth_config)
    ship_config.update(dict(
        color='green',
        lambda_offset=ship_true_anomaly,
        planet_r=2,
        mass=10000,
        a_config=(),
        start_velocity=ship_start_velocity,
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
        if not os.path.exists(RESULT_DIRECTORY):
            os.makedirs(RESULT_DIRECTORY)

        self.canvas = canvas
        self.pack_propagate(0)
        self.with_ship = BooleanVar(self, value=True)
        self.delta_t = DoubleVar(self, value=DELTA_T)
        self.start_velocity = DoubleVar(self, value=START_VELOCITY)

        self.runner = None
        self.planets = self.objects_with_custom_accelerations = ()
        self.earth = self.mars = self.ship = self.sun = None
        self.acceleration_settings_near_earth = []
        self.acceleration_settings_near_mars = []
        self.acceleration_settings_near_sun = []
        self.file_to_write = None
        self.write_logs_to_file = BooleanVar(self, value=False)
        self.init_ui()

    def init_ui(self):
        exit_button = Button(self, text='Quit', command=self.quit, bg='#ffaaaa')
        exit_button.pack(side=BOTTOM)

        fr = Frame(self)
        fr.pack(side=TOP)
        self.delta_t_label = Label(fr, text='Time step (delta_t)')
        self.delta_t_label.pack(side=LEFT)
        self.delta_t_widget = Entry(fr, textvariable=self.delta_t)
        self.delta_t_widget.pack(side=RIGHT)

        fr = Frame(self)
        fr.pack(side=TOP)
        self.start_velocity_label = Label(fr, text='Start ship velocity')
        self.start_velocity_label.pack(side=LEFT)
        self.start_velocity_widget = Entry(fr, textvariable=self.start_velocity)
        self.start_velocity_widget.pack(side=RIGHT)

        write_logs_to_file_button = Checkbutton(
            self, text='Write logs to file',
            variable=self.write_logs_to_file,
        )
        write_logs_to_file_button.pack()

        self.setup_true_anomaly_setting_fields()

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

        self.earth_acc_group = LabelFrame(self, text='Ship Acceleration settings near The Earth')
        self.earth_acc_group.pack(side=TOP)
        self.setup_ship_earth_acceleration_setting_fields()
        add_earth_acc_config = Button(self, text='ADD CONDITION', command=self.add_earth_acceleration_condition, bg='#aaddff')
        add_earth_acc_config.config(width=20, height=4)
        add_earth_acc_config.pack(side=TOP)

        self.mars_acc_group = LabelFrame(self, text='Ship Acceleration settings near The Mars')
        self.mars_acc_group.pack(side=TOP)
        self.setup_ship_mars_acceleration_setting_fields()
        add_mars_acc_config = Button(self, text='ADD CONDITION', command=self.add_mars_acceleration_condition, bg='#aaddff')
        add_mars_acc_config.config(width=20, height=4)
        add_mars_acc_config.pack(side=TOP)

        self.sun_acc_group = LabelFrame(self, text='Ship Acceleration settings near The Sun')
        self.sun_acc_group.pack(side=TOP)
        self.setup_ship_sun_acceleration_setting_fields()
        add_sun_acc_config = Button(self, text='ADD CONDITION', command=self.add_sun_acceleration_condition, bg='#aaddff')
        add_sun_acc_config.config(width=20, height=4)
        add_sun_acc_config.pack(side=TOP)

    def setup_true_anomaly_setting_fields(self):
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
        self.mars_true_anomaly_widget.insert(INSERT, 244)

        fr3 = Frame(group)
        fr3.pack(side=TOP)
        self.ship_true_anomaly_label = Label(fr3, text='Ship True Anomaly')
        self.ship_true_anomaly_label.pack(side=LEFT)
        self.ship_true_anomaly_widget = Entry(fr3)
        self.ship_true_anomaly_widget.pack(side=RIGHT)
        self.ship_true_anomaly_widget.insert(INSERT, 260)

    def setup_ship_earth_acceleration_setting_fields(self):
        self.fr_earth_acc = Frame(self.earth_acc_group)
        self.fr_earth_acc.pack(side=TOP)
        if not self.acceleration_settings_near_earth:
            return

        a_label = Label(self.fr_earth_acc, text='Del')
        a_label.grid(row=0, column=0)
        a_widget = Label(self.fr_earth_acc, text='Distance')
        a_widget.grid(row=0, column=1)
        a_dist_widget = Label(self.fr_earth_acc, text='Acceleration')
        a_dist_widget.grid(row=0, column=2)

        for i, (distance, acc) in enumerate(self.acceleration_settings_near_earth):

            def remove_earth_acc_condition(i=i):
                def execute():
                    self.acceleration_settings_near_earth.pop(i)
                    self.fr_earth_acc.destroy()
                    self.setup_ship_earth_acceleration_setting_fields()
                return execute

            w_r = Button(self.fr_earth_acc, text='X', command=remove_earth_acc_condition(), bg='#aaddff')
            w_r.grid(row=i + 1, column=0)
            w_d = Entry(self.fr_earth_acc, textvariable=distance)
            w_d.grid(row=i + 1, column=1)
            w_a = Entry(self.fr_earth_acc, textvariable=acc)
            w_a.grid(row=i + 1, column=2)

    def add_earth_acceleration_condition(self):
        self.acceleration_settings_near_earth.append((DoubleVar(), DoubleVar()),)
        self.fr_earth_acc.destroy()
        self.setup_ship_earth_acceleration_setting_fields()

    def setup_ship_mars_acceleration_setting_fields(self):
        self.fr_mars_acc = Frame(self.mars_acc_group)
        self.fr_mars_acc.pack(side=TOP)
        if not self.acceleration_settings_near_mars:
            return

        a_label = Label(self.fr_mars_acc, text='Del')
        a_label.grid(row=0, column=0)
        a_widget = Label(self.fr_mars_acc, text='Distance')
        a_widget.grid(row=0, column=1)
        a_dist_widget = Label(self.fr_mars_acc, text='Acceleration')
        a_dist_widget.grid(row=0, column=2)

        for i, (distance, acc) in enumerate(self.acceleration_settings_near_mars):

            def remove_mars_acc_condition(i=i):
                def execute():
                    self.acceleration_settings_near_mars.pop(i)
                    self.fr_mars_acc.destroy()
                    self.setup_ship_mars_acceleration_setting_fields()
                return execute

            w_r = Button(self.fr_mars_acc, text='X', command=remove_mars_acc_condition(), bg='#aaddff')
            w_r.grid(row=i + 1, column=0)
            w_d = Entry(self.fr_mars_acc, textvariable=distance)
            w_d.grid(row=i + 1, column=1)
            w_a = Entry(self.fr_mars_acc, textvariable=acc)
            w_a.grid(row=i + 1, column=2)

    def add_mars_acceleration_condition(self):
        self.acceleration_settings_near_mars.append((DoubleVar(), DoubleVar()),)
        self.fr_mars_acc.destroy()
        self.setup_ship_mars_acceleration_setting_fields()

    def setup_ship_sun_acceleration_setting_fields(self):
        self.fr_sun_acc = Frame(self.sun_acc_group)
        self.fr_sun_acc.pack(side=TOP)
        if not self.acceleration_settings_near_sun:
            return

        a_label = Label(self.fr_sun_acc, text='Del')
        a_label.grid(row=0, column=0)
        a_widget = Label(self.fr_sun_acc, text='Distance')
        a_widget.grid(row=0, column=1)
        a_dist_widget = Label(self.fr_sun_acc, text='Acceleration')
        a_dist_widget.grid(row=0, column=2)

        for i, (distance, acc) in enumerate(self.acceleration_settings_near_sun):

            def remove_sun_acc_condition(i=i):
                def execute():
                    self.acceleration_settings_near_sun.pop(i)
                    self.fr_sun_acc.destroy()
                    self.setup_ship_sun_acceleration_setting_fields()
                return execute

            w_r = Button(self.fr_sun_acc, text='X', command=remove_sun_acc_condition(), bg='#aaddff')
            w_r.grid(row=i + 1, column=0)
            w_d = Entry(self.fr_sun_acc, textvariable=distance)
            w_d.grid(row=i + 1, column=1)
            w_a = Entry(self.fr_sun_acc, textvariable=acc)
            w_a.grid(row=i + 1, column=2)

    def add_sun_acceleration_condition(self):
        self.acceleration_settings_near_sun.append((DoubleVar(), DoubleVar()),)
        self.fr_sun_acc.destroy()
        self.setup_ship_sun_acceleration_setting_fields()

    def get_acceleration_config(self):
        return {
            'ship_earth_a_config': [(float(d.get()), float(a.get())) for d, a in self.acceleration_settings_near_earth],
            'ship_mars_a_config': [(float(d.get()), float(a.get())) for d, a in self.acceleration_settings_near_mars],
            'ship_sun_a_config': [(float(d.get()), float(a.get())) for d, a in self.acceleration_settings_near_sun],
        }

    def init_start_positions(self):
        self.canvas.delete(ALL)
        if self.runner is not None:
            self.master.after_cancel(self.runner)

        try:
            velocity = self.start_velocity.get()
        except:
            velocity = None

        configs = get_planet_configs(
            int(self.canvas['width']),
            int(self.canvas['height']),
            velocity,
            earth_true_anomaly=float(self.earth_true_anomaly_widget.get()),
            mars_true_anomaly=float(self.mars_true_anomaly_widget.get()),
            ship_true_anomaly=float(self.ship_true_anomaly_widget.get()),
            **self.get_acceleration_config()
        )
        scale = configs['scale']

        self.earth = Planet('Earth', self.canvas, scale, **configs['earth_config'])
        self.mars = Planet('Mars', self.canvas, scale, **configs['mars_config'])

        self.planets = (
            self.earth,
            self.mars,
        )
        if self.with_ship.get():
            self.ship = Planet('Ship', self.canvas, scale, **configs['ship_config'])
            self.objects_with_custom_accelerations = (self.ship,)
        else:
            self.ship, self.objects_with_custom_accelerations = None, ()

        self.sun = Planet('Sun', self.canvas, scale, **configs['sun_config'])

        if self.file_to_write:
            self.file_to_write.close()
            self.file_to_write = None
        if self.objects_with_custom_accelerations and self.write_logs_to_file.get():
            file_name_prefix = '%s/%s' % (RESULT_DIRECTORY, FILE_NAME_PREFIX)
            files_count = len([
                name for name in os.listdir(RESULT_DIRECTORY)
                if os.path.isfile('%s/%s' % (RESULT_DIRECTORY, name)) and FILE_NAME_PREFIX in name
            ])
            file_name = '%s%s.txt' % (file_name_prefix, ' (%s)' % files_count if files_count else '')
            if self.file_to_write:
                self.file_to_write.close()
            self.file_to_write = open(file_name, 'w')
            self.file_to_write.write(
                'Time\tVelocity Ship-Sun\tVelocity Ship-Sun X\tVelocity Ship-Sun Y\t'
                'Distance Ship-Sun\tVelocity Ship-Earth\t'
                'Distance Ship-Earth\tVelocity Ship-Mars\tDistance Ship-Mars\n'
            )
        self.time = 0
        self.resume_running()

    def run_system(self, sun, planets, objects_with_custom_accelerations):
        results = iter(get_get_new_positions(
            sun,
            planets=planets,
            delta_t=self.delta_t.get(),
            objects_with_custom_accelerations=objects_with_custom_accelerations,
        ))
        for (x, v_x, y, v_y), p in zip(chunkinate_iterable(results, 4),
                                       chain(planets, objects_with_custom_accelerations)):
            p.move(x, y)
            p.left_trace_dot()
            p.set_coordinates_and_velocity(x, v_x, y, v_y)
        self.time += self.delta_t.get()
        if objects_with_custom_accelerations and self.write_logs_to_file.get():
            ship, = objects_with_custom_accelerations
            to_file_data = '%s\t%s\t%s\t%s\t%s\t' % (
                self.time, math.sqrt(ship.v_x ** 2 + ship.v_y ** 2),
                ship.v_x, ship.v_y, math.sqrt(ship.x ** 2 + ship.y ** 2),
            )
            for p in planets:
                rel_v_x = ship.v_x - p.v_x
                rel_v_y = ship.v_y - p.v_y
                rel_x = ship.x - p.x
                rel_y = ship.y - p.y
                to_file_data += '%s\t%s\t' % (
                    math.sqrt(rel_v_x ** 2 + rel_v_y ** 2),
                    math.sqrt(rel_x ** 2 + rel_y ** 2),
                )
            to_file_data += '\n'
            self.file_to_write.write(to_file_data)
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
