from tkinter import Tk

from earth_mars_ship_diff import Gui


def run():
    root = Tk()
    root.config(background="#FFFFFF")
    app = Gui(root)
    root.mainloop()


if __name__ == '__main__':
    run()
