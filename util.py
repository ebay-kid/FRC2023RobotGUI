import math

import PIL.ImageFile
import numpy as np

from constants import FIELD_WIDTH_IMG, FIELD_WIDTH_REAL_M


# apply zoom to coordinate
def zoom_coordinate(x, y, zoom_x, zoom_y, factor):
    return x + (x - zoom_x) * (factor - 1), y + (y - zoom_y) * (factor - 1)


# apply reverse zoom
def reverse_zoom(x, y, zoom_x, zoom_y, factor):
    return (x + (factor - 1) * zoom_x) / factor, (y + (factor - 1) * zoom_y) / factor


# gets the coordinates from trajectory states
def get_coords(state):
    return meters_to_pixels(state.pose.X()), meters_to_pixels(state.pose.Y())


# pixel to meter conversion
def pixels_to_meters(pixels):
    return pixels * FIELD_WIDTH_REAL_M / FIELD_WIDTH_IMG


# meter to pixel conversion
def meters_to_pixels(meters):
    return meters * FIELD_WIDTH_IMG / FIELD_WIDTH_REAL_M


# normalize angle to [0, 360], while allowing a small delta to equal 0.
def normalize_angle(angle, normalize=False):
    angle %= 360
    if angle < 0:
        angle += 360
    if normalize and abs(360 - angle) < 0.5:
        angle = 0
    return angle


# distance formula calculation
def distance(x1, y1, x2, y2):
    return math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2))


# fix file name
def fix_npy_file_name(file_name: str) -> str:
    if not file_name.endswith('.npy'):
        file_name += '.npy'
    return file_name


def image_path(name: str) -> str:
    return "imgs/" + name + ("" if name.endswith(".png") else ".png")


def npy_path(name: str) -> str:
    return "trajectories/real/" + name + ("" if name.endswith(".npy") else ".npy")


def average(sequence) -> float:
    return sum(sequence) / len(sequence)


# flatten image to be used as Texture
def flat_img(mat: PIL.ImageFile) -> np.ndarray:
    mat.putalpha(255)
    dpg_image = np.frombuffer(mat.tobytes(), dtype=np.uint8) / 255.0
    return dpg_image


def rotate(v, cos, sin) -> np.ndarray:
    return np.array((v[0] * cos - v[1] * sin, v[0] * sin + v[1] * cos))


def angle_between_points(a, b, c):
    # Coordinates of points A, B, C
    x1, y1 = a
    x2, y2 = b
    x3, y3 = c

    # Vectors AB and BC
    ab = (x2 - x1, y2 - y1)
    bc = (x3 - x2, y3 - y2)

    # Dot product of AB and BC
    dot_product = ab[0] * bc[0] + ab[1] * bc[1]

    # Magnitudes of AB and BC
    mag_ab = math.sqrt(ab[0] ** 2 + ab[1] ** 2)
    mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)

    # Cosine of the angle
    cos_theta = dot_product / (mag_ab * mag_bc)

    # Ensure the value is within the domain of acos due to floating-point precision
    cos_theta = max(-1.0, min(1.0, cos_theta))

    # Angle in radians
    angle_rad = math.acos(cos_theta)

    # Convert angle to degrees
    angle_deg = math.degrees(angle_rad)

    return angle_deg
