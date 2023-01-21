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

MAXIMUM_WAYPOINTS = 4

DEFINED_WAYPOINTS = [
    (395, 945),  #enter straightaway (rightside)
    (395, 1085), #enter straightaway (rightside)
    (60,945),    #enter straightaway (leftside)
    (60,1085),   #enter straightaway (leftside)
    (489,401),
]
POSED_WAYPOINTS = [True,True,True,True,False]

def writeToFile(arr: np.ndarray, fileName: str):
    print("iohefoiwhatruipaewhrf8iueasbgulfasge7ufgyuasiejfguilsdzgfuildzskgfd")
    with open(fileName, 'wb') as f:
        np.save(f, arr)

def readFromFile(fileName: str) -> np.ndarray:
    with open(fileName, 'rb') as f:
        return np.load(f)

#gets the coordinates from trajectory states
def getCoords(state):
    return (meterstoPixels(state.pose.X()), meterstoPixels(state.pose.Y()))

#pixel to meter conversion
def pixeltoMeters(pixels):
    return pixels*0.012

#meter to pixel conversion
def meterstoPixels(meters):
    return meters/0.012

def normalizeAngle(angle):
    angle %= 360
    if angle < 0:
        angle += 360
    if abs(360-angle) < 0.5:
      angle = 0
    return angle

#probably not going to work on this if the other stuff works
def findOptimalWaypoint():
    print("yeah i'm pretty much screwed here")

#find bounary issues and request waypoint calculation
def fixBoundaryTrespassing(coords, waypoints, used_waypoints):
    with open('boundariesBalls.npy', 'rb') as f:
        boundaries = np.load(f)
        coordscount = len(coords[0])
        for i in range(coordscount):
            if not boundaries[int(coords[1][i])][int(coords[0][i])]:
                blockedX = coords[0][i]
                blockedY = coords[1][i]
                minDistance = 1000000
                waypointIndex = 0
                for ind,i in enumerate(DEFINED_WAYPOINTS):
                    testDistance = distance(i[0],i[1],blockedX,blockedY)
                    if testDistance < minDistance and not used_waypoints[ind]:
                        waypointIndex = ind
                        minDistance = testDistance
                used_waypoints[waypointIndex] = True
                previousPose = waypoints[len(waypoints)-2]
                nextPose = waypoints[-1]
                curX = pixeltoMeters(DEFINED_WAYPOINTS[waypointIndex][0])
                curY = pixeltoMeters(DEFINED_WAYPOINTS[waypointIndex][1])
                if POSED_WAYPOINTS[waypointIndex]:
                    optimalAngle = 90
                else:
                    optimalAngle = findOptimalAngleInBetween(previousPose.X(),previousPose.Y(),curX,curY,nextPose.X(),nextPose.Y())
                waypoints.insert((len(waypoints)-1),pose(curX,curY,optimalAngle))
                waypoints[-1] = pose(nextPose.X(),nextPose.Y(),findOptimalAngle(curX,curY,nextPose.X(),nextPose.Y()))

                return True
        return False

#distance formula calculation
def distance(x1,y1,x2,y2):
    return math.sqrt(math.pow((x1-x2),2)+math.pow((y1-y2),2))

#find most optimalAngle
def findOptimalAngle(prevX,prevY,curX,curY):
    y = prevY - curY
    x = prevX - curX
    return normalizeAngle((math.atan2(y,x) * 180 / math.pi)+180)

def findOptimalAngleInBetween(prevX,prevY,curX,curY,nextX,nextY):
    y = prevY - curY
    x = prevX - curX
    y2 = curY - nextY
    x2 = curX - nextX
    a1 = normalizeAngle((math.atan2(y,x) * 180 / math.pi)+180)
    a2 = normalizeAngle((math.atan2(y2,x2) * 180 / math.pi)+180)
    return (a1 + a2) / 2

#create Pose2D object
def pose(x,y,rot):
    return geometry.Pose2d(x,y,geometry.Rotation2d.fromDegrees(rot))

getCoordsVectorized = np.vectorize(getCoords)
# creates the trajectory
def generate(waypoints):
    configSettings = trajectory.TrajectoryConfig(MAX_SPEED_MPS,MAX_ACCELERATION_MPS_SQUARED)
    configSettings.setKinematics(DRIVE_KINEMATICS)
    #configSettings.setReversed(True);
    new_trajectory = trajectory.TrajectoryGenerator.generateTrajectory(
        waypoints,
        configSettings
    )

    states = np.array(new_trajectory.states())
    #uploadStates(new_trajectory)
    return getCoordsVectorized(states)

def load():
    traject = readFromFile("trajectory.npy")


#Main handler of trajectory generation
def generateTrajectoryVector(startX,startY,startAngle,endX,endY):
    #check if trajectory is "VALID"
    with open('boundariesBalls.npy', 'rb') as f:
        boundaries = np.load(f)
        if not boundaries[int(endY)][int(endX)]:
            return

    endAngle = findOptimalAngle(startX,startY,endX,endY)

    #init waypoints
    waypoints = [pose(pixeltoMeters(startX),pixeltoMeters(startY),startAngle),pose(pixeltoMeters(endX),pixeltoMeters(endY),endAngle)]

    global used_waypoints
    used_waypoints = np.zeros(len(DEFINED_WAYPOINTS),dtype=bool)

    #find most optimal ending angle

    coords = generate(waypoints) #generate inital trajectory
    if(fixBoundaryTrespassing(coords, waypoints, used_waypoints)):
        coords = generate(waypoints)
    if(fixBoundaryTrespassing(coords, waypoints, used_waypoints)):
        coords = generate(waypoints)

    importantPoints = []
    for i in waypoints:
        importantPoints.append((meterstoPixels(i.X()),meterstoPixels(i.Y())))
    return importantPoints, coords

def uploadStates(traject: trajectory):
    TICK_TIME = 0.02 # 20 ms

    trajTime = traject.Trajectory.totalTime()
    numOfStates = math.ceil(trajTime / TICK_TIME)
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

    writeToFile(upload, "trajectory.npy")

def parseStates(arr: np.ndarray):
    states = []
    if arr.size % 7 != 0 or arr.size == 0:
        raise ValueError("Array size must be divisible by 7")
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