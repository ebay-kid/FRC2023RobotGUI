import numpy as np
import math
from wpimath import trajectory, geometry, kinematics
import network_tables

from constants import *
from util import *

#MPS = Meters Per Second
MAX_SPEED_MPS = 3
MAX_ACCELERATION_MPS_SQUARED = 1
DRIVE_KINEMATICS = kinematics.DifferentialDriveKinematics(trackWidth=57.15)

KS_VOLTS = 0.22
KV_VOLTS_SECONDS_PER_METER = 1.98
KA_VOLTS_SECONDS_SQ_PER_METER = 0.2

MAXIMUM_WAYPOINTS = 4

DEFINED_WAYPOINTS = [
    (395, 945),  #enter straightaway (rightside)
    (395, 1085), #enter straightaway (rightside)
    (60, 945),    #enter straightaway (leftside)
    (60, 1085),   #enter straightaway (leftside)
    (489, 401),
]
POSED_WAYPOINTS = [True,True,True,True,False]

most_recent_trajectory: trajectory.Trajectory = None

def getMostRecentTrajectory() -> trajectory.Trajectory:
    return most_recent_trajectory

def writeToFile(arr: np.ndarray, fileName: str):
    with open(fileName, 'wb') as f:
        np.save(f, arr)

def readFromFile(fileName: str) -> np.ndarray:
    with open(fileName, 'rb') as f:
        return np.load(f)

def saveWaypoints(waypoints: list, fileName: str):
    arr = np.array(waypoints)
    writeToFile(arr, fileName)

def loadWaypoints(fileName: str) -> list:
    arr = readFromFile(fileName)
    return arr.tolist()

#find bounary issues and request waypoint calculation
def fixBoundaryTrespassing(coords, waypoints, used_waypoints):
    boundaries = readFromFile(npy_path('boundariesBalls'))
    coordscount = len(coords[0])
    for i in range(coordscount):
        if not boundaries[int(coords[1][i])][int(coords[0][i])]:
            blockedX = coords[0][i]
            blockedY = coords[1][i]
            minDistance = 1000000
            waypointIndex = 0
            for ind, i in enumerate(DEFINED_WAYPOINTS):
                testDistance = distance(i[0], i[1], blockedX, blockedY)
                if testDistance < minDistance and not used_waypoints[ind]:
                    waypointIndex = ind
                    minDistance = testDistance
            used_waypoints[waypointIndex] = True
            previousPose = waypoints[len(waypoints) - 2]
            nextPose = waypoints[-1]
            curX = pixels_to_meters(DEFINED_WAYPOINTS[waypointIndex][0])
            curY = pixels_to_meters(DEFINED_WAYPOINTS[waypointIndex][1])
            if POSED_WAYPOINTS[waypointIndex]:
                optimalAngle = 90
            else:
                optimalAngle = findOptimalAngleInBetween(previousPose.X(), previousPose.Y(), curX, curY, nextPose.X(), nextPose.Y())
            waypoints.insert((len(waypoints) - 1), pose(curX, curY, optimalAngle))
            waypoints[-1] = pose(nextPose.X(), nextPose.Y(), findOptimalAngle(curX, curY, nextPose.X(), nextPose.Y()))

            return True
    return False

#find most optimalAngle
def findOptimalAngle(prevX, prevY, curX, curY):
    y = prevY - curY
    x = prevX - curX
    return normalize_angle((math.atan2(y, x) * 180 / math.pi) + 180)

def findOptimalAngleInBetween(prevX, prevY, curX, curY, nextX, nextY):
    y = prevY - curY
    x = prevX - curX
    y2 = curY - nextY
    x2 = curX - nextX
    a1 = normalize_angle((math.atan2(y, x) * 180 / math.pi) + 180)
    a2 = normalize_angle((math.atan2(y2, x2) * 180 / math.pi) + 180)
    return (a1 + a2) / 2

def listOfPointsToTrajectory(points: list, initialRotation: float):
    initial = pose(pixels_to_meters(points[0][0]), pixels_to_meters(points[0][1]), initialRotation)
    waypoints = []
    for i in range(1, len(points) - 1):
        waypoints.append(geometry.Translation2d(pixels_to_meters(points[i][0]), pixels_to_meters(points[i][1])))
    end = geometry.Pose2d(pixels_to_meters(points[-1][0]), pixels_to_meters(points[-1][1]), findOptimalAngle(pixels_to_meters(points[-2][0]), pixels_to_meters(points[-2][1]), pixels_to_meters(points[-1][0]), pixels_to_meters(points[-1][1])))
    return generateFromStart_Waypoints(initial, waypoints, end)

#create Pose2D object
def pose(x, y, rot) -> geometry.Pose2d:
    return geometry.Pose2d(x, y, geometry.Rotation2d.fromDegrees(rot))

vectorizedGetCoords = np.vectorize(get_coords)
# creates the trajectory
def generateFromStart_End(waypoints: list):
    global most_recent_trajectory
    
    configSettings = trajectory.TrajectoryConfig(MAX_SPEED_MPS, MAX_ACCELERATION_MPS_SQUARED)
    configSettings.setKinematics(DRIVE_KINEMATICS)
    #configSettings.setReversed(True);
    new_trajectory = trajectory.TrajectoryGenerator.generateTrajectory(
        waypoints,
        configSettings
    )

    most_recent_trajectory = new_trajectory

    states = np.array(new_trajectory.states())
    uploadStates(new_trajectory)
    return vectorizedGetCoords(states)

def generateFromStart_Waypoints(start: geometry.Pose2d, waypoints: list, end: geometry.Pose2d):
    global most_recent_trajectory

    configSettings = trajectory.TrajectoryConfig(MAX_SPEED_MPS, MAX_ACCELERATION_MPS_SQUARED)
    configSettings.setKinematics(DRIVE_KINEMATICS)
    #configSettings.setReversed(True);
    new_trajectory = trajectory.TrajectoryGenerator.generateTrajectory(
        start=start,
        interiorWaypoints=waypoints,
        end=end,
        config=configSettings
    )

    most_recent_trajectory = new_trajectory

    states = np.array(new_trajectory.states())
    uploadStates(new_trajectory)
    return vectorizedGetCoords(states)

def coordsFromTrajectory(traject: trajectory.Trajectory):
    states = np.array(traject.states())
    return vectorizedGetCoords(states)

#Main handler of trajectory generation
def generateTrajectoryVector(startX, startY, startAngle, endX, endY):
    #check if trajectory is "VALID"
    with open(npy_path('boundariesBalls'), 'rb') as f:
        boundaries = np.load(f)
        if not boundaries[int(endY)][int(endX)]:
            return

    endAngle = findOptimalAngle(startX,startY,endX,endY) # for our usecase, end angle doesn't matter and we just need the angle requiring the least movement.

    #init waypoints
    waypoints = [pose(pixels_to_meters(startX), pixels_to_meters(startY), startAngle), pose(pixels_to_meters(endX), pixels_to_meters(endY), endAngle)]

    global used_waypoints
    used_waypoints = np.zeros(len(DEFINED_WAYPOINTS), dtype=bool)

    #find most optimal ending angle

    coords = generateFromStart_End(waypoints) #generate inital trajectory
    if(fixBoundaryTrespassing(coords, waypoints, used_waypoints)):
        coords = generateFromStart_End(waypoints)
    if(fixBoundaryTrespassing(coords, waypoints, used_waypoints)):
        coords = generateFromStart_End(waypoints)

    importantPoints = []
    for i in waypoints:
        importantPoints.append((meters_to_pixels(i.X()), meters_to_pixels(i.Y())))
    return importantPoints, coords

def uploadStates(traject: trajectory.Trajectory, ntUpload = True):
    TICK_TIME = 0.02 # 20 ms

    trajTime = traject.totalTime()
    numOfStates = math.ceil(trajTime / TICK_TIME)
    upload = np.empty(7 * numOfStates) # this can only be sent as a 1-D array.

    state: trajectory.Trajectory.State
    for i in range(numOfStates):
        currTime = TICK_TIME * i
        state = traject.sample(t=currTime)

        shift = i * 7
        # 0 = timeSeconds; 1 = velocity m/s; 2 = acceleration m/s^2; (3, 4, 5) = x, y, rotation rad -> Pose2D; 6 = curvation rad/m
        upload[shift + 0] = state.t
        upload[shift + 1] = state.velocity
        upload[shift + 2] = state.acceleration
        upload[shift + 3] = state.pose.X()
        upload[shift + 4] = state.pose.Y()
        upload[shift + 5] = state.pose.rotation().radians()
        upload[shift + 6] = state.curvature

    if ntUpload and USINGNETWORKTABLES:
        network_tables.get_entry("robogui", "trajectory").setDoubleArray(upload)

    # writeToFile(upload, npy_path("trajectory"))

def parseStates(arr: np.ndarray) -> trajectory.Trajectory:
    states = []
    if arr.size % 7 != 0 or arr.size == 0:
        raise ValueError("Array size must be divisible by 7 and non-zero.")
    for i in range(arr.size // 7):
        shift = i * 7
        time = arr[shift + 0]
        velocity = arr[shift + 1]
        acceleration = arr[shift + 2]
        x = arr[shift + 3]
        y = arr[shift + 4]
        rotation = arr[shift + 5]
        curvature = arr[shift + 6]
        states.append(trajectory.Trajectory.State(time, velocity, acceleration, geometry.Pose2d(x, y, geometry.Rotation2d(rotation)), curvature))
    return trajectory.Trajectory(states)
