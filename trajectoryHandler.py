
import numpy as np
from wpimath import trajectory, geometry, kinematics

#MPS = Meters Per Second
MAX_SPEED_MPS = 3
MAX_ACCELERATION_MPS_SQUARED = 1
DRIVE_KINEMATICS = kinematics.DifferentialDriveKinematics(trackWidth = 0.69)

KS_VOLTS = 0.22
KV_VOLTS_SECONDS_PER_METER = 1.98
KA_VOLTS_SECONDS_SQ_PER_METER = 0.2

def fastestSplineCoords(startX,startY,startAngle,endX,endY,endAngle):
    return [geometry.Translation2d(0,-50), geometry.Translation2d(0,50)]


def getCoords(state):
    return (state.pose.X(),state.pose.Y())

def generateTrajectoryVector(startX,startY,startAngle,endX,endY,endAngle):
    startPoint = geometry.Pose2d(startX,startY,geometry.Rotation2d(startAngle))
    endPoint = geometry.Pose2d(endX,endY,geometry.Rotation2d(endAngle))
    easePoints = fastestSplineCoords(startX,startY,startAngle,endX,endY,endAngle)
    configSettings = trajectory.TrajectoryConfig(MAX_SPEED_MPS,MAX_ACCELERATION_MPS_SQUARED)
    configSettings.setKinematics(DRIVE_KINEMATICS)
    new_trajectory = trajectory.TrajectoryGenerator.generateTrajectory(
        startPoint,
        easePoints,
        endPoint,
        configSettings
    )

    states = np.array(new_trajectory.states())
    getCoordsVectorized = np.vectorize(getCoords)
    return getCoordsVectorized(states)
    