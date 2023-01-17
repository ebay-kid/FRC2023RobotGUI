import numpy as np
import math
from wpimath import trajectory, geometry, kinematics
import network_tables

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
      angle = 0
    return angle

def fixBoundaryTrespassing(coords):
    with open('boundariesBalls.npy', 'rb') as f:
        boundaries = np.load(f)
        coordscount = len(coords[0])
        for i in range(coordscount):
            if not boundaries[int(coords[1][i])][int(coords[0][i])]:
                return (int(coords[0][i]),int(coords[1][i]))
        return (0,0)

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
    uploadStates(new_trajectory)
    getCoordsVectorized = np.vectorize(getCoords)
    return getCoordsVectorized(states)

def generateTrajectoryVector(startX,startY,startAngle,endX,endY):
    #init waypoints
    global waypoints
    waypoints = []

    #find most optimal ending angle
    y = startY - endY
    x = startX - endX
    endAngle = normalizeAngle((math.atan2(y,x) * 180 / math.pi)+180)
    coords = generate(startX,startY,startAngle,endX,endY,endAngle) #generate straight line

    #keep adding waypoints until robot's path is clear
    return fixBoundaryTrespassing(coords), coords

def uploadStates(traject: trajectory):
    TICK_TIME = 0.02 # 20 ms

    trajTime = traject.Trajectory.totalTime()
    numOfStates = trajTime // TICK_TIME
    upload = np.empty(7 * numOfStates) # this can only be sent as a 1-D array.

    state: trajectory.Trajectory.State
    for i in range(numOfStates):
        currTime = TICK_TIME * i
        state = traject.Trajectory.sample(t=currTime)

        shift = i * 7
        # 0 = timeSeconds; 1 = velocity m/s; 2 = acceleration m/s^2; (3, 4, 5) = x, y, rotation rad -> Pose2D; 6 = curvation rad/m
        upload[shift + 0] = state.t
        upload[shift + 1] = state.velocity
        upload[shift + 2] = state.acceleration
        upload[shift + 3] = state.pose.X()
        upload[shift + 4] = state.pose.Y()
        upload[shift + 5] = state.pose.rotation().radians
        upload[shift + 6] = state.curvature
    network_tables.getEntry("robogui", "trajectory").setDoubleArray(upload)