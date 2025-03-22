import ntcore
import time
import threading
from constants import IS_ROBOT_SIM


def wait_for_connect():
    """
    Waits for the robot to connect to the driver station.
    """
    while not is_connected():
        time.sleep(0.5)
    print("Connected to robot!")


# Initialize ntcore on protocol 4
inst = ntcore.NetworkTableInstance.getDefault()
startThread = threading.Thread(target=wait_for_connect)


def is_connected():
    """
    network tables takes like 15 secs to connect to the robot if the robot was already on when this code launched.\n
    if you just re-deploy code *after* launching this program then the time is only the time to initialize the robot code.\n
    so just run this program first then initialize robot to save time
    """
    default_check_str = "this is not fms info"  # This should be a string value that cannot be achieved on the robot and will be present on the robot at any given point
    # if the robot is connected to the driver station, since this wil be set to something else if connected properly.
    return inst.getTable("FMSInfo").getEntry(".type").getString(default_check_str) != default_check_str


def init():
    """
    Initializes the network tables client. This should be called before any other functions in this module.
    """
    inst.startClient4("DS GUI Controller")
    inst.setServerTeam(3952)
    if IS_ROBOT_SIM:
        inst.setServer("127.0.0.1")
    inst.startDSClient()

    startThread.start()


def get_instance():
    """
    Returns the network tables instance.
    """
    return inst


def get_table(table_name):
    """
    Returns a table from the network tables server.
    """
    if not is_connected():
        print("Not connected to robot!")
    return inst.getTable(table_name)


def get_entry(table_name, entry_name):
    """
    Returns an entry from a table from the network tables server.
    """
    if not is_connected():
        print("Not connected to robot!")
    return inst.getTable(table_name).getEntry(entry_name)


# init()

def latency_test():
    """
    Use NetworkTables#latencyTesterPeriodicRun() in the periodic of robot to test latency.
    """
    entry = get_entry("test", "test")
    i = 0.1
    while True:
        time.sleep(1)
        i += 0.1
        entry.setDoubleArray([i, i, i])

#
# #Get values from NetworkTables
# robotCoordTag = sd.getEntry("RobotCoord")
# scaleTag = sd.getEntry("Scale")
# mouseCoordTag = sd.getEntry("MouseCoord")
#
# #Set values to NetworkTables
# robotCoordTag.setDoubleArray([latestX, latestY])
# scaleTag.setDouble(gameScale)
# mouseCoordTag.setDoubleArray([mouseX, mouseY])
#
# #Get values from NetworkTables
# robotCoord = robotCoordTag.getDoubleArray([0,0])
# scale = scaleTag.getDouble(1)
# mouseCoord = mouseCoordTag.getDoubleArray([0,0])
