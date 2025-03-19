# Handles storing the raw field data in its true form
# All variables are as if they were on the actual robot (blue alliance origin, meters)

import numpy as np


class Robot:
    def __init__(self, x: float, y: float, rot_deg: float, opacity: float):
        self.x = x
        self.y = y
        self.rot = rot_deg
        self.opacity = opacity


class Trajectory:
    def __init__(self, points: np.ndarray[np.ndarray[np.float64]]):
        self.points = points


if __name__ == "__main__":
    r1 = Robot(1., 2., 3., 4.)
