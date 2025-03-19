import math
from constants import FIELDHEIGHT_IMG, FIELDHEIGHT_REAL_M


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
    return pixels * FIELDHEIGHT_REAL_M / FIELDHEIGHT_IMG


# meter to pixel conversion
def meters_to_pixels(meters):
    return meters * FIELDHEIGHT_IMG / FIELDHEIGHT_REAL_M


# normalize angle to [0, 360], while allowing a small delta to equal 0.
def normalize_angle(angle):
    angle %= 360
    if angle < 0:
        angle += 360
    if abs(360 - angle) < 0.5:
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
