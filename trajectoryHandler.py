import numpy as np
import math
from wpimath import trajectory, geometry, kinematics

#MPS = Meters Per Second
MAX_SPEED_MPS = 3
MAX_ACCELERATION_MPS_SQUARED = 1
DRIVE_KINEMATICS = kinematics.DifferentialDriveKinematics(trackWidth = 57.15)

KS_VOLTS = 0.22
KV_VOLTS_SECONDS_PER_METER = 1.98
KA_VOLTS_SECONDS_SQ_PER_METER = 0.2

DEFINED_WAYPOINTS = [
(383, 159),
(383, 302),
(74, 159),
(74, 425),
(495, 580),
(391, 876),
(531, 1006)
]

#global Waypoints
waypoints = []

def getCoords(state):
    return (meterstoPixels(state.pose.X()),meterstoPixels(state.pose.Y()))

def pixeltoMeters(pixels):
    return pixels*0.012

def meterstoPixels(meters):
    return meters/0.012

def normalizeAngle(angle):
    angle %= 360
    if angle < 0:
        angle += 360
    if abs(360-angle) < 0.5:
      angle = 0;
    return angle

#this fucking trajectroy code doesn't fucking work i want to die someone please fix this
def fixBoundaryTrespassing(coords):
    with open('boundariesBalls.npy', 'rb') as f:
        boundaries = np.load(f)
        coordscount = len(coords[0])
        for i in range(coordscount):
            if not boundaries[int(coords[1][i])][int(coords[0][i])]:
                wayPointIndex = 0
                minWayPoint = 100000
                for k,possibleWaypoint in enumerate(DEFINED_WAYPOINTS):
                    dist = distance(possibleWaypoint[0],possibleWaypoint[1],coords[1][i],coords[0][i])
                    if dist < minWayPoint:
                        minWayPoint = dist
                        wayPointIndex = k
                waypoints.append(DEFINED_WAYPOINTS[wayPointIndex])
                return True
        return False

def distance(x1,y1,x2,y2):
    return math.sqrt(math.pow((x1-x2),2)+math.pow((y1-y2),2))

def generate(startX,startY,startAngle,endX,endY,endAngle):
    startPoint = geometry.Pose2d(pixeltoMeters(startX),pixeltoMeters(startY),geometry.Rotation2d.fromDegrees(startAngle))
    endPoint = geometry.Pose2d(pixeltoMeters(endX),pixeltoMeters(endY),geometry.Rotation2d.fromDegrees(endAngle))
    configSettings = trajectory.TrajectoryConfig(MAX_SPEED_MPS,MAX_ACCELERATION_MPS_SQUARED)
    configSettings.setKinematics(DRIVE_KINEMATICS)
    #configSettings.setReversed(True);

    new_trajectory = trajectory.TrajectoryGenerator.generateTrajectory(
        startPoint,
        waypoints,
        endPoint,
        configSettings
    )

    states = np.array(new_trajectory.states())
    getCoordsVectorized = np.vectorize(getCoords)
    return getCoordsVectorized(states)

def generateTrajectoryVector(startX,startY,startAngle,endX,endY):
    #init waypoints
    global waypoints
    waypoints = []

    #find most optimal ending angle
    y = startY - endY
    x = startX - endX
    endAngle = normalizeAngle((math.atan2(y,x) * 180 / math.pi)+180);
    coords = generate(startX,startY,startAngle,endX,endY,endAngle) #generate straight line

    #keep adding waypoints until robot's path is clear
    while(True):
        if not fixBoundaryTrespassing(coords):
            break
        else:
            coords = generate(startX,startY,startAngle,endX,endY,endAngle)
    return coords
    