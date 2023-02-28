import numpy as np
import dearpygui.dearpygui as dpg
import time 
from PIL import Image
import pyautogui
import ctypes
import trajectoryHandler
import tkinter.filedialog as fd
import os
from wpimath import trajectory

from util import *

#intialize user32 to read monitor size
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

#for framerate calculations
prev_frame_time = 0
new_frame_time = 0

#Constants
ENABLEVSYNC = True
SCREENWIDTH = user32.GetSystemMetrics(0)
SCREENHEIGHT = user32.GetSystemMetrics(1)
FIELDWIDTH_PX = 660
FIELDHEIGHT_PX = 1305
CLICK_RADIUS_ACCEPTED = 40

#Global Tags
mouseCoordTag = 0

#dynamically updating global variables
trajectoryCoords = np.zeros((500, 500))
latestX = 0
latestY = 0
gameScale = 1

waypoints = [] # Array of clicked waypoints

# draw coordinate global variables
tDraw = [] # trajectories
bDraw = [0] * 2 # background
rDraw = [0] * 2 # robot
intersectCoord = (0, 0) # Intersections of blocked areas (ignored in this program because we assume manually added trajectories will properly move themselves around blocked areas)

targetedDropoffLocation = 1 # The targeted location to drop off the item
clickedElement = "" # stored as "wp_" + index or "tr_" + index, where index is the index of the element within the respective arrays. "" if no element is selected

selectedWaypoints = []

def noop():
    """Utility function to run no-callback"""
    pass

# mouse callback function, called when mouse is clicked.
currentMouseCallback = noop

# update FPS
def updateFps():
    global new_frame_time
    global prev_frame_time
    new_frame_time = time.time()
    fps = 1 / (new_frame_time-prev_frame_time + 0.000001)
    prev_frame_time = new_frame_time
    return "FPS " + str(int(fps))

# flatten image to be used as Texture
def flat_img(mat):
    mat.putalpha(255)
    dpg_image = np.frombuffer(mat.tobytes(), dtype=np.uint8) / 255.0
    return dpg_image

# redraw all elements
def update_graphics():
    global trajectoryCoords
    global selectedWaypoints

    # Render setup
    dpg.set_item_height("drawlist", FIELDHEIGHT_PX)
    dpg.set_item_width("drawlist", FIELDWIDTH_PX)
    if dpg.does_alias_exist:
        dpg.delete_item("drawlist", children_only=True)

    # Render our field image
    dpg.draw_image("game field", (0,0), (FIELDWIDTH_PX, FIELDHEIGHT_PX), uv_min=(0, 0), uv_max=(1,1), parent="drawlist")

    # Render waypoints
    for i in range(len(waypoints)):
        x, y = waypoints[i][0], waypoints[i][1]
        id = "wp_" + str(i)
        if dpg.does_alias_exist(id):
            dpg.delete_item(id)

        # Colors the first waypoint a different color,
        # If the waypoint is selected, color it a different color to indicate its selection
        if i == 0:
            if i in selectedWaypoints:
                dpg.draw_circle((x, y), 5, fill=(0, 255, 255, 255), parent="drawlist", tag=id)
            else:
                dpg.draw_circle((x, y), 5, fill=(0, 0, 255, 255), parent="drawlist", tag=id) # Initial point
        else:
            if i in selectedWaypoints: # Color the selected waypoints a different color as a visual indicator
                dpg.draw_circle((x, y), 5, fill=(0, 255, 0, 255), parent="drawlist", tag=id)
            else:
                dpg.draw_circle((x, y), 5, fill=(255, 0, 0, 255), parent="drawlist", tag=id)
    
    # Render the trajectory path
    tDraw = np.zeros(np.shape(trajectoryCoords))
    for i in range(np.shape(trajectoryCoords)[1]):
        tDraw[0][i], tDraw[1][i] = trajectoryCoords[0][i], trajectoryCoords[1][i]
    for i in range(np.shape(trajectoryCoords)[1] - 1):
        x, y = tDraw[0][i], tDraw[1][i]
        id = "tr_" + str(i)
        if dpg.does_alias_exist(id):
            dpg.delete_item(id)
        dpg.draw_line((x, y), (tDraw[0][i + 1], tDraw[1][i + 1]), color=(255, 0, 0, 255), thickness=3, parent="drawlist", tag=id)
    traj = trajectoryHandler.getMostRecentTrajectory()
    time = 0
    if traj is not None:
        time = traj.totalTime()
    dpg.set_value("trajectoryEstTime", f"Estimated time: {time:.2f} sec")


def findDrawnElementByCoord(x, y):
    """Given an (x, y), find the element that was clicked (within a small radius)"""
    global CLICK_RADIUS_ACCEPTED
    global trajectoryCoords
    global waypoints
    global clickedElement

    hasSet = False
    for i in range(len(waypoints)):
        coord = waypoints[i]
        dist = distance(coord[0], coord[1], x, y)
        if dist <= CLICK_RADIUS_ACCEPTED:
            clickedElement = "wp_" + str(i)
            hasSet = True
            break
    if not hasSet:
        for i in range(np.shape(trajectoryCoords)[1]):
            coord = (trajectoryCoords[0][i], trajectoryCoords[1][i])
            dist = distance(coord[0], coord[1], x, y)
            if dist <= CLICK_RADIUS_ACCEPTED:
                clickedElement = "tr_" + str(i)
                hasSet = True
                break
    if not hasSet:
        clickedElement = ""

def reloadSelectedWaypointsTextbox():
    dpg.set_value("selected_wps", str(selectedWaypoints))

def getTimeAtLocation(waypoint_idx):
    waypoint = waypoints[waypoint_idx]
    waypoint = (pixeltoMeters(waypoint[0]), pixeltoMeters(waypoint[1])) # i guess?
    print(waypoint)
    for state in trajectoryHandler.getMostRecentTrajectory().states():
        if distance(state.pose.x, state.pose.y, waypoint[0], waypoint[1]) < 0.5:
            return f"{state.t:.2f}"
    return "-1.00"

def toggleTrajModMode():
    """Toggles trajectory modification mode"""
    global currentMouseCallback
    def selectWaypoint():
        global selectedWaypoints
        global waypoints
        global clickedElement
        global currentMouseCallback

        if clickedElement is not None and clickedElement.startswith("wp_"):
            if len(selectedWaypoints) < 2:
                selectedWaypoints.append(int(clickedElement[3:]))
                if(len(selectedWaypoints) == 2):
                    if selectedWaypoints[0] == selectedWaypoints[1]:
                        selectedWaypoints.pop()
                    elif selectedWaypoints[0] > selectedWaypoints[1]:
                        selectedWaypoints.reverse()
            else:
                currentMouseCallback = noop
        traj = trajectoryHandler.getMostRecentTrajectory()
        states: list[trajectory.Trajectory.State] = traj.states
        
        dpg.set_value("waypointTimeStamps", f"Seconds at each waypoint: {', '.join(getTimeAtLocation(i) for i in selectedWaypoints)}")
        reloadSelectedWaypointsTextbox()
    if dpg.get_value("traj_mod_mode"):
        currentMouseCallback = selectWaypoint
    else:
        currentMouseCallback = noop
        selectedWaypoints.clear()
        reloadSelectedWaypointsTextbox()

def insertWP():
    """Inserts a waypoint between the two selected waypoints"""
    global currentMouseCallback
    def waypointInsertion():
        # On click, insert waypoint at the clicked location between the curerntly selected indices of currently existing waypoints
        global waypoints
        global selectedWaypoints
        global latestX, latestY
        global currentMouseCallback

        if len(selectedWaypoints) < 2:
            return

        # Insert waypoint at the clicked location
        waypoints.insert(selectedWaypoints[0] + 1, (latestX, latestY))
        selectedWaypoints.clear()
        reloadSelectedWaypointsTextbox()
        update_graphics()
        currentMouseCallback = toggleTrajModMode
    currentMouseCallback = waypointInsertion

def deleteWP():
    """Deletes the selected waypoint (if there are multiple selected, removes the 1st element)"""
    global currentMouseCallback
    global waypoints
    global selectedWaypoints

    if len(selectedWaypoints) > 1:
        return

    # Delete waypoint
    waypoints.pop(selectedWaypoints[0])
    selectedWaypoints.clear()
    reloadSelectedWaypointsTextbox()
    update_graphics()

def moveWP():
    """Moves the selected waypoint (if there are multiple selected, moves the 1st element)"""
    global currentMouseCallback

    def waypointMovement():
        # On click, move waypoint to the clicked location
        global waypoints
        global selectedWaypoints
        global latestX, latestY
        global currentMouseCallback

        if len(selectedWaypoints) > 1:
            return

        # Move waypoint
        waypoints[selectedWaypoints[0]] = (latestX, latestY)
        selectedWaypoints.clear()
        reloadSelectedWaypointsTextbox()
        update_graphics()
        currentMouseCallback = toggleTrajModMode
    currentMouseCallback = waypointMovement
    reloadSelectedWaypointsTextbox()

#create trajectory
def clickCapturer():
    """A general callback for clicks."""
    global latestX
    global latestY
    global waypoints

    latestX = max(pyautogui.position()[0] - 10, 0)
    latestY = max(pyautogui.position()[1] - 25, 0)

    if latestX > FIELDWIDTH_PX or latestY > FIELDHEIGHT_PX:
        return

    dpg.set_value(mouseCoordTag, "CLICK: X " + str(latestX) + " Y " + str(latestY))

    # if button traj_mod_mode is true, then we are in modify mode
    if dpg.get_value("traj_mod_mode"):
        findDrawnElementByCoord(latestX, latestY)
        currentMouseCallback()
    else:
        waypoints.append((latestX, latestY))
    update_graphics()

def keypress(sender, app_data):
    """Captures keypress (hotkeys and stuff)"""
    global targetedDropoffLocation
    if app_data >= 48 and app_data <= 57:
        targetedDropoffLocation = app_data - 48

def checkInWaypointsOrCloseBy(arr: list, target):
    """
    Cast the arr list 0, 1 to ints, then check if distance is within delta of target
    """
    for i in range(np.shape(arr)[0]):
        dist = distance(int(arr[i][0]), int(arr[i][1]), target[0], target[1])
        if dist <= 5:
            return i
    return None

#main APP CONTROL
def main():
    global waypoints

    #always create context first
    dpg.create_context()
    
    #get image and convert to 1D array to turn into a static texture
    img = Image.open(image_path("gamefield"))
    img_rotated = img.rotate(-90, expand=True)
    dpg_image = flat_img(img_rotated)

    #load all textures
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=FIELDWIDTH_PX, height=FIELDHEIGHT_PX, default_value=dpg_image, tag="game field")

    #create viewport
    dpg.create_viewport(title='Team 3952', width=SCREENWIDTH, height=SCREENHEIGHT)
    dpg.set_viewport_vsync(ENABLEVSYNC)
    dpg.setup_dearpygui()
    dpg.toggle_viewport_fullscreen()
    dpg.set_global_font_scale(3)

    #basically an event handler
    with dpg.handler_registry():
        dpg.add_mouse_click_handler(callback=clickCapturer)
        dpg.add_key_press_handler(callback=keypress)
    
    #create window for drawings and images
    with dpg.window(tag="Window1"):
        dpg.set_primary_window("Window1", True)
        with dpg.drawlist(tag="drawlist", width=SCREENWIDTH / 3, height=FIELDHEIGHT_PX, parent="Window1"):
            dpg.draw_image("game field", (0, 0), (FIELDWIDTH_PX, FIELDHEIGHT_PX), uv_min=(0, 0), uv_max=(1, 1))

    #create window for text 
    with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(450, 250), pos=(SCREENWIDTH / 3 + 20, 10)):
        global mouseCoordTag
        fpsTag = dpg.add_text("FPS 0")
        mouseCoordTag = dpg.add_text("CLICKED: X 0 Y 0")

    def popWaypoint():
        """Unselects the most recently selected waypoint"""
        waypoints.pop()
        update_graphics()

    def generateTrajectory():
        """Generates a trajectory"""
        global trajectoryCoords
        trajectoryCoords = trajectoryHandler.listOfPointsToTrajectory(waypoints, 0)
        update_graphics()
    
    def saveTrajectory():
        """Saves the trajectory by asking where it should be saved"""
        global trajectoryCoords
        global waypoints

        file = fd.asksaveasfile(mode='w', filetypes=[('Numpy Save files', '*.npy')], title='Save Trajectory File')
        fName = fixNpyFileName(file.name)
        file.close()
        os.remove(file.name) # when you close the file then it trolls and makes the file with a potentially bad name, so delete and then save with the fixed name afterwards.
        trajectoryHandler.writeToFile(trajectoryCoords, fName)
        trajectoryHandler.saveWaypoints(waypoints, fName + "_waypoints.npy")

    def loadTrajectory():
        """Loads trajectory from chosen file"""
        global trajectoryCoords
        global waypoints

        file = fd.askopenfile(mode='r', filetypes=[('Numpy Save files', '*.npy')], title='Select Trajectory File')
        fName = fixNpyFileName(file.name)
        file.close()
        trajectoryCoords = trajectoryHandler.readFromFile(file.name)

        waypoints = trajectoryHandler.loadWaypoints(fName + "_waypoints.npy")
        update_graphics()

    def clearTrajectory():
        """Removes all waypoints"""
        global trajectoryCoords
        waypoints.clear()
        trajectoryCoords = np.zeros((0, 0))
        update_graphics()

    with dpg.window(tag="trajGenWindow", label="Trajectory Generation", no_close=True, min_size=(450, 350), pos=(SCREENWIDTH / 3 + 20, 300)):
        dpg.add_button(label="Remove last point", callback=popWaypoint)
        dpg.add_button(label="Generate Trajectory", callback=generateTrajectory)
        dpg.add_button(label="Save Trajectory", callback=saveTrajectory)
        dpg.add_button(label="Load Trajectory", callback=loadTrajectory)
        dpg.add_button(label="Clear Trajectory", callback=clearTrajectory)

    with dpg.window(tag="trajModification", label="Trajectory Modification", no_close=True, min_size=(650, 350), pos=(SCREENWIDTH / 3 + 20, 600)):
        dpg.add_checkbox(tag="traj_mod_mode", label="Trajectory Modification Mode", callback=toggleTrajModMode)
        dpg.add_button(tag="insert_wp", label="Insert Point Between Waypoints", callback=insertWP)
        dpg.add_button(tag="remove_wp", label="Remove Selected Point", callback=deleteWP)
        dpg.add_button(tag="move_wp", label="Move Selected Point", callback=moveWP)
        dpg.add_text(tag="selected_wps", default_value="Selected Waypoints: None")

    with dpg.window(tag="trajInfoWindow", label="Trajectory Info", no_close=True, min_size=(850, 350), pos=(SCREENWIDTH / 3 + 500, 10)):
        dpg.add_text(tag="trajectoryEstTime", default_value="Estimated time: 0 sec")
        dpg.add_text(tag="waypointTimeStamps", default_value="Seconds at each waypoint: []")

    #show viewport
    dpg.show_viewport()

    #run program
    while dpg.is_dearpygui_running():
        dpg.set_value(fpsTag, updateFps())    
        dpg.render_dearpygui_frame()                      

    dpg.destroy_context()
    os._exit(0)

if __name__ == "__main__":
    main()