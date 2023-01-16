import numpy as np
from wpimath import trajectory, geometry, kinematics

#MPS = Meters Per Second
MAX_SPEED_MPS = 3
MAX_ACCELERATION_MPS_SQUARED = 1
DRIVE_KINEMATICS = kinematics.DifferentialDriveKinematics(trackWidth = 0.69)

KS_VOLTS = 0.22
KV_VOLTS_SECONDS_PER_METER = 1.98
KA_VOLTS_SECONDS_SQ_PER_METER = 0.2

def calculateWaypoints():
    with open('boundariesTEST.npy', 'rb') as f:
        boundaries = np.load(f)
    return []



def getCoords(state):
    return (meterstoPixels(state.pose.X()),meterstoPixels(state.pose.Y()))

def pixeltoMeters(pixels):
    return pixels*0.012

def meterstoPixels(meters):
    return meters/0.012

def generateTrajectoryVector(startX,startY,startAngle,endX,endY,endAngle):
    startPoint = geometry.Pose2d(pixeltoMeters(startX),pixeltoMeters(startY),geometry.Rotation2d.fromDegrees(startAngle))
    endPoint = geometry.Pose2d(pixeltoMeters(endX),pixeltoMeters(endY),geometry.Rotation2d.fromDegrees(endAngle))
    easePoints = calculateWaypoints()
    configSettings = trajectory.TrajectoryConfig(MAX_SPEED_MPS,MAX_ACCELERATION_MPS_SQUARED)
    configSettings.setKinematics(DRIVE_KINEMATICS)
    #configSettings.setReversed(True);

    new_trajectory = trajectory.TrajectoryGenerator.generateTrajectory(
        startPoint,
        easePoints,
        endPoint,
        configSettings
    )

    states = np.array(new_trajectory.states())
    getCoordsVectorized = np.vectorize(getCoords)
    return getCoordsVectorized(states)
    
print(generateTrajectoryVector(200,200,0,400,700,0))