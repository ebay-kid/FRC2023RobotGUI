# Handles storing the raw field data in its true form
# All variables are as if they were on the actual robot (blue alliance origin, meters)

import numpy as np
from util import meters_to_pixels, pixels_to_meters
from constants import FIELD_HEIGHT_IMG


class Robot:
    def __init__(self, x: float, y: float, rot_deg: float, opacity: float):
        self.x = x
        self.y = y
        self.rot = rot_deg
        self.opacity = opacity


class Trajectory:
    def __init__(self, points: np.ndarray[np.ndarray[np.float64]]):
        self.points = points


def field_to_screen(x: float, y: float):
    # Screen y increases as it goes down the screen, against common sense
    # X increases linearly
    return meters_to_pixels(x), FIELD_HEIGHT_IMG - meters_to_pixels(y)

def screen_to_field(x: float, y: float):
    # see field_to_screen
    return pixels_to_meters(x), pixels_to_meters(FIELD_HEIGHT_IMG - y)


if __name__ == "__main__":
    r1 = Robot(1., 2., 3., 4.)
