from tkinter import Tk, Canvas

# from earth_mars import init_start_positions
from earth_mars_ship import init_start_positions


CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 1000


def run():
    root = Tk()
    canvas = Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
    canvas.pack()
    init_start_positions(root, canvas)
    root.mainloop()


if __name__ == '__main__':
    run()
