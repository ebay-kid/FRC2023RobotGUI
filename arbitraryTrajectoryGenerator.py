import numpy as np
import dearpygui.dearpygui as dpg
import time 
from PIL import Image
import pyautogui
import ctypes
import trajectoryHandler
import tkinter.filedialog as fd
import os

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
FIELDWIDTH = 660
FIELDHEIGHT = 1305

#Global Tags
mouseCoordTag = 0

#dynamically updating global variables
trajectoryCoords = np.zeros((500, 500))
latestX = 0
latestY = 0
gameScale = 1

waypoints = []

#draw coordinate global variables
tDraw = [] #trajectories
bDraw = [0] * 2 #background
rDraw = [0] * 2 #robot
intersectCoord = (0, 0)

targetedDropoffLocation = 1
clickedElement = "" # stored as "wp_" + index or "tr_" + index, where index is the index of the element within the respective arrays. "" if no element is selected

selectedWaypoints = []

def noop():
    pass

# mouse callback function, called when mouse is clicked. should take in x and y coordinates rep. current mouse position
currentMouseCallback = noop

#update FPS
def updateFps():
    global new_frame_time
    global prev_frame_time
    new_frame_time = time.time()
    fps = 1 / (new_frame_time-prev_frame_time + 0.000001)
    prev_frame_time = new_frame_time
    return "FPS " + str(int(fps))

#flatten image to be used as Texture
def flat_img(mat):
    mat.putalpha(255)
    dpg_image = np.frombuffer(mat.tobytes(), dtype=np.uint8) / 255.0
    return dpg_image

#redraw all elements
def update_graphics():
    global trajectoryCoords

    dpg.set_item_height("drawlist", FIELDHEIGHT)
    dpg.set_item_width("drawlist", FIELDWIDTH)
    if dpg.does_alias_exist:
        dpg.delete_item("drawlist", children_only=True)
    dpg.draw_image("game field", (0,0), (FIELDWIDTH, FIELDHEIGHT), uv_min=(0, 0), uv_max=(1,1), parent="drawlist")

    for i in range(len(waypoints)):
        x, y = waypoints[i][0], waypoints[i][1]
        id = "wp_" + str(i)
        if dpg.does_alias_exist(id):
            dpg.delete_item(id)
        if i == 0:
            dpg.draw_circle((x, y), 5, fill=(0, 0, 255, 255), parent="drawlist", tag=id) # Initial point
        else:
            dpg.draw_circle((x, y), 5, fill=(255, 0, 0, 255), parent="drawlist", tag=id) # All other waypoints
    
    tDraw = np.zeros(np.shape(trajectoryCoords))
    for i in range(np.shape(trajectoryCoords)[1]):
        tDraw[0][i], tDraw[1][i] = trajectoryCoords[0][i], trajectoryCoords[1][i]
    for i in range(np.shape(trajectoryCoords)[1] - 1):
        x, y = tDraw[0][i], tDraw[1][i]
        id = "tr_" + str(i)
        if dpg.does_alias_exist(id):
            dpg.delete_item(id)
        dpg.draw_line((x, y), (tDraw[0][i + 1], tDraw[1][i + 1]), color=(255, 0, 0, 255), thickness=3, parent="drawlist", tag=id)

def findDrawnElementByCoord(x, y):
    global trajectoryCoords
    global waypoints
    global clickedElement

    hasSet = False
    for i in range(len(waypoints)):
        coord = waypoints[i]
        dist = distance(coord[0], coord[1], x, y)
        if dist <= 50:
            clickedElement = "wp_" + str(i)
            hasSet = True
            break
    if not hasSet:
        for i in range(np.shape(trajectoryCoords)[1]):
            coord = (trajectoryCoords[0][i], trajectoryCoords[1][i])
            dist = distance(coord[0], coord[1], x, y)
            if dist <= 50:
                clickedElement = "tr_" + str(i)
                hasSet = True
                break
    if not hasSet:
        clickedElement = ""
    print("clickedElem: ", clickedElement)

def insertWP():
    global currentMouseCallback
    def waypointInsertion():
        # On click, insert waypoint at the clicked location between the curerntly selected indices of currently existing waypoints
        global waypoints
        global selectedWaypoints
    currentMouseCallback = waypointInsertion

def deleteWP():
    pass

#create trajectory
def clickCapturer():
    global latestX
    global latestY
    global waypoints

    latestX = max(pyautogui.position()[0] - 10, 0)
    latestY = max(pyautogui.position()[1] - 25, 0)

    if latestX > FIELDWIDTH or latestY > FIELDHEIGHT:
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
    global targetedDropoffLocation
    if app_data >= 48 and app_data <= 57:
        targetedDropoffLocation = app_data - 48

def checkInWaypointsOrCloseBy(arr: list, target):
    """
    Cast the arr list 0, 1 to ints, then check if distance is within delta of target
    """
    print("arr shape: ", np.shape(arr))
    print("target:", target)
    for i in range(np.shape(arr)[0]):
        print("arr[i]:", arr[i])
        dist = distance(int(arr[i][0]), int(arr[i][1]), target[0], target[1])
        # print("dist:", dist)
        if dist <= 5:
            print("double copium gaming")
            return i
    return None

#main APP CONTROL
def main():
    global waypoints

    #always create context first
    dpg.create_context()
    
    #get image and convert to 1D array to turn into a static texture
    img = Image.open('gamefield.png')
    img_rotated = img.rotate(-90, expand=True)
    dpg_image = flat_img(img_rotated)

    #load all textures
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=FIELDWIDTH, height=FIELDHEIGHT, default_value=dpg_image, tag="game field")

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
        with dpg.drawlist(tag="drawlist", width=SCREENWIDTH / 3, height=FIELDHEIGHT, parent="Window1"):
            dpg.draw_image("game field", (0, 0), (FIELDWIDTH, FIELDHEIGHT), uv_min=(0, 0), uv_max=(1, 1))

    #create window for text 
    with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(450, 250), pos=(SCREENWIDTH / 3 + 20, 10)):
        global mouseCoordTag
        fpsTag = dpg.add_text("FPS 0")
        mouseCoordTag = dpg.add_text("CLICKED: X 0 Y 0")

    def popWaypoint():
        waypoints.pop()
        update_graphics()

    def generateTrajectory():
        global trajectoryCoords
        trajectoryCoords = trajectoryHandler.listOfPointsToTrajectory(waypoints, 0)
        update_graphics()
    
    def saveTrajectory():
        global trajectoryCoords
        global waypoints

        file = fd.asksaveasfile(mode='w', filetypes=[('Numpy Save files', '*.npy')], title='Save Trajectory File')
        fName = fixNpyFileName(file.name)
        file.close()
        os.remove(file.name) # when you close the file then it trolls and makes the file with a potentially bad name, so delete and then save with the fixed name afterwards.
        trajectoryHandler.writeToFile(trajectoryCoords, fName)
        trajectoryHandler.saveWaypoints(waypoints, fName + "_waypoints.npy")

    def loadTrajectory():
        global trajectoryCoords
        global waypoints

        file = fd.askopenfile(mode='r', filetypes=[('Numpy Save files', '*.npy')], title='Select Trajectory File')
        fName = fixNpyFileName(file.name)
        file.close()
        trajectoryCoords = trajectoryHandler.readFromFile(file.name)

        waypoints = trajectoryHandler.loadWaypoints(fName + "_waypoints.npy")
        update_graphics()

    def clearTrajectory():
        global trajectoryCoords
        waypoints.clear()
        trajectoryCoords = np.zeros((0, 0))
        update_graphics()

    def toggleTrajModMode():
        global currentMouseCallback
        def selectWaypoint(x, y):
            global selectedWaypoints
            global waypoints
            global clickedElement
            global currentMouseCallback

            if clickedElement is not None and clickedElement.startswith("wp_"):
                if len(selectedWaypoints) < 2:
                    selectedWaypoints.append(int(clickedElement[3:]))
                    if selectedWaypoints[0] == selectedWaypoints[1]:
                        selectedWaypoints.pop()
                    elif selectedWaypoints[0] > selectedWaypoints[1]:
                        selectedWaypoints.reverse()
                else:
                    currentMouseCallback = noop
        currentMouseCallback = selectWaypoint if dpg.get_value("traj_mod_mode") else noop

    with dpg.window(tag="trajGenWindow", label="Trajectory Generation", no_close=True, min_size=(450, 350), pos=(SCREENWIDTH / 3 + 20, 300)):
        dpg.add_button(label="Remove last point", callback=popWaypoint)
        dpg.add_button(label="Generate Trajectory", callback=generateTrajectory)
        dpg.add_button(label="Save Trajectory", callback=saveTrajectory)
        dpg.add_button(label="Load Trajectory", callback=loadTrajectory)
        dpg.add_button(label="Clear Trajectory", callback=clearTrajectory)

    with dpg.window(tag="trajModification", label="Trajectory Modification", no_close=True, min_size=(550, 350), pos=(SCREENWIDTH / 3 + 20, 600)):
        dpg.add_checkbox(tag="traj_mod_mode", label="Trajectory Modification Mode", callback=toggleTrajModMode)
        dpg.add_button(tag="insert_wp", label="Insert Point Between Waypoints", callback=insertWP)
        dpg.add_button(tag="remove_wp", label="Remove Selected Point", callback=deleteWP)
        dpg.add_text(tag="selected_wps", default_value="Selected Waypoints: None")

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