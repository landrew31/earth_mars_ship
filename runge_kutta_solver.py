import numpy as np


def get_k_addon(functions, previous, delta_t):

    def get_coef(args):
        return delta_t * np.array([func(*args) for func in functions])

    previous = np.array(previous)
    k1 = get_coef(previous)
    k2 = get_coef(previous + 1 / 2 * k1)
    k3 = get_coef(previous + 1 / 2 * k2)
    k4 = get_coef(previous + k3)
    return 1 / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


def solve_runge_kutta(functions, previous, delta_t):
    previous = np.array(previous)
    return list(previous + get_k_addon(functions, previous, delta_t))
