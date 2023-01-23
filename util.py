import math

#apply zoom to coordinate
def zoom_coordinate(x, y, zoomX, zoomY, factor):
    return x + (x - zoomX) * (factor - 1), y + (y - zoomY) * (factor - 1)

#apply reverse zoom
def reverse_zoom(x, y, zoomX, zoomY, factor):
    return (x + (factor - 1) * zoomX) / factor, (y + (factor - 1) * zoomY) / factor

#gets the coordinates from trajectory states
def getCoords(state):
    return (meterstoPixels(state.pose.X()), meterstoPixels(state.pose.Y()))

#pixel to meter conversion
def pixeltoMeters(pixels):
    return pixels * 0.012

#meter to pixel conversion
def meterstoPixels(meters):
    return meters / 0.012

#normalize angle to [0, 360], while allowing a small delta to equal 0.
def normalizeAngle(angle):
    angle %= 360
    if angle < 0:
        angle += 360
    if abs(360 - angle) < 0.5:
      angle = 0
    return angle

#distance formula calculation
def distance(x1, y1, x2, y2):
    return math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2))