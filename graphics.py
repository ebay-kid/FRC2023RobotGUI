import os
import dearpygui.dearpygui as dpg
import time 
import numpy as np
from PIL import Image
import ctypes
from constants import ROBOTHEIGHT_REAL_M, ROBOTLENGTH_REAL_M
from trajectoryHandler import generateTrajectoryVector
import pyautogui
import network_tables
from constants import *
from util import *

import collections

from util import meterstoPixels

#intialize user32 to read monitor size
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

#for framerate calculations
prev_frame_time = 0
new_frame_time = 0

# some constants
SCREENWIDTH = user32.GetSystemMetrics(0)
SCREENHEIGHT = user32.GetSystemMetrics(1)
FPS_RECORD_DELAY = 4

#dynamically updating global variables
trajectoryCoords = np.zeros((500, 500))
intersectCoords = np.zeros((20, 2))
latestX = 0
latestY = 0
gameScale = 1

#Global Tags
robotCoordTag = 0
scaleTag = 0
mouseCoordTag = 0

MAX_FPS = 2000
fps_record_delay_count = FPS_RECORD_DELAY
fps_record = collections.deque(maxlen=100)

#Connect to NetworkTables
if USINGNETWORKTABLES and __name__ == "__main__":
    network_tables.init()
    while not network_tables.isConnected():
        time.sleep(0.3)

#Initialize and Values using NetworkTables
teamColor = True #True = Blue, False = Red
robotX = 400
robotY = 600
robotAngle = 0

def nah(sender, app_data):
    pass

def average(sequence) -> float:
    return sum(sequence) / len(sequence)

# Gets the raw fps, which can be very wrong
def get_raw_fps():
    global new_frame_time, prev_frame_time
    new_frame_time = time.time()
    fps = 1/(new_frame_time-prev_frame_time+0.000001)
    prev_frame_time = new_frame_time
    return fps

# Gets the fps, but with some extra steps to clean the values.
def get_clean_fps():
    global fps_record_delay_count
    fps = get_raw_fps()
    fps_record_delay_count += 1
    if fps <= MAX_FPS and fps_record_delay_count >= FPS_RECORD_DELAY:
        fps_record.appendleft(fps)
        fps_record_delay_count = 0
    return average(fps_record)
    
#update FPS
def updateFps():
    fps = get_clean_fps()
    return f"FPS {fps:.1f}"

#flatten image to be used as Texture
def flat_img(mat):
    mat.putalpha(255)
    dpg_image = np.frombuffer(mat.tobytes(), dtype=np.uint8) / 255.0
    return dpg_image


ROBOTLENGTH_IMG = meterstoPixels(ROBOTLENGTH_REAL_M)
ROBOTHEIGHT_IMG = meterstoPixels(ROBOTHEIGHT_REAL_M)

#redraw all elements
def update_graphics():
    trajectoryDraw = np.zeros(np.shape(trajectoryCoords))
    backgroundDraw = [0] * 2
    robotDraw = [0] * 2
    for i in range(np.shape(trajectoryCoords)[1]):
        trajectoryDraw[0][i], trajectoryDraw[1][i] = zoom_coordinate(trajectoryCoords[0][i], trajectoryCoords[1][i], robotX, robotY, gameScale)
    backgroundDraw[0] = zoom_coordinate(0, 0, robotX, robotY, gameScale)
    backgroundDraw[1] = zoom_coordinate(FIELDWIDTH_IMG, FIELDHEIGHT_IMG, robotX, robotY, gameScale)
    robotDraw[0] = zoom_coordinate(robotX - ROBOTLENGTH_IMG, robotY - ROBOTHEIGHT_IMG, robotX, robotY, gameScale)
    robotDraw[1] = zoom_coordinate(robotX + ROBOTLENGTH_IMG, robotY + ROBOTHEIGHT_IMG, robotX, robotY, gameScale)

    dpg.set_item_height("drawlist", FIELDHEIGHT_IMG)
    dpg.set_item_width("drawlist", FIELDWIDTH_IMG)
    if dpg.does_alias_exist:
        dpg.delete_item("drawlist", children_only=True)
    dpg.draw_image("game field", backgroundDraw[0], backgroundDraw[1], uv_min=(0, 0), uv_max=(1,1), parent="drawlist")
    dpg.draw_image("robot texture", robotDraw[0], robotDraw[1], uv_min=(0, 0), uv_max=(1, 1), parent="drawlist")
    for i in range(np.shape(trajectoryCoords)[1] - 1):
        dpg.draw_line((trajectoryDraw[0][i], trajectoryDraw[1][i]), (trajectoryDraw[0][i + 1], trajectoryDraw[1][i + 1]), color=(255, 0, 0, 255), thickness=3, parent="drawlist")

#create trajectory
def createTrajectory():
    global intersectCoords
    global trajectoryCoords
    global latestX
    global latestY
    prevX = latestX
    prevY = latestY
    latestX, latestY = reverse_zoom(max(pyautogui.position()[0] - 10, 0), max(pyautogui.position()[1] - 25, 0), robotX, robotY, gameScale)

    if(latestX > FIELDWIDTH_IMG or latestY > FIELDHEIGHT_IMG):
        latestX = prevX
        latestY = prevY
        return

    dpg.set_value(mouseCoordTag, "GOAL: X " + str(latestX) + " Y " + str(latestY))

    if(robotY < latestY):
        tempAngle = robotAngle+90
    else:
        tempAngle = robotAngle-90
    intersectCoords, trajectoryCoords = generateTrajectoryVector(robotX, robotY, tempAngle, latestX, latestY)
    update_graphics()

#main APP CONTROL
def main():
    #always create context first
    dpg.create_context()
    
    #get image and convert to 1D array to turn into a static texture
    img = Image.open(image_path('field_2025_s'))
    robotImg = Image.open(image_path('robot_2025'))
    if teamColor:
        img_rotated = img.rotate(0, expand=True)
    else:
        img_rotated = img.rotate(180, expand=True)
        
    dpg_image = flat_img(img_rotated)
    dpg_image2 = flat_img(robotImg)
    width2 = robotImg.width
    height2 = robotImg.height
    #load all textures
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=FIELDWIDTH_IMG, height=FIELDHEIGHT_IMG, default_value=dpg_image, tag="game field")
        dpg.add_static_texture(width=width2, height=height2, default_value=dpg_image2, tag="robot texture")

    #create viewport
    dpg.create_viewport(title='Team 3952', width=SCREENWIDTH, height=SCREENHEIGHT)
    dpg.set_viewport_vsync(ENABLEVSYNC)
    dpg.setup_dearpygui()
    dpg.toggle_viewport_fullscreen()
    dpg.set_global_font_scale(3)

    #mouse wheel scaling
    def scale_image(sender, app_data):
        global gameScale
        gameScale += (app_data * 0.05)
        if gameScale < 1:
            gameScale = 1
        else:
            update_graphics()
        dpg.set_value(scaleTag, "SCALE " + str(round(gameScale, 2)) + "x")

    #basically an event handler
    with dpg.handler_registry():
        dpg.add_mouse_wheel_handler(callback=scale_image)
        dpg.add_mouse_click_handler(callback=createTrajectory)
        dpg.add_mouse_drag_handler(callback=nah)
    
    #create window for drawings and images
    with dpg.window(tag="Window1", no_scroll_with_mouse=True):
        dpg.set_primary_window("Window1", True)
        with dpg.drawlist(tag="drawlist", width=FIELDWIDTH_IMG, height=FIELDHEIGHT_IMG, parent="Window1"):
            dpg.draw_image("game field", (0, 0), (FIELDWIDTH_IMG, FIELDHEIGHT_IMG), uv_min=(0, 0), uv_max=(1, 1))
            dpg.draw_image("robot texture", (robotX - ROBOTLENGTH_IMG / 2, robotY - ROBOTHEIGHT_IMG / 2), (robotX + ROBOTLENGTH_IMG / 2, robotY + ROBOTHEIGHT_IMG / 2), uv_min=(0, 0), uv_max=(1, 1))

    #create window for text 
    with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(450, 250), pos=(SCREENWIDTH / 2 + 20, 10)):
        global mouseCoordTag
        global robotCoordTag
        global scaleTag
        fpsTag = dpg.add_text("FPS 0")
        scaleTag = dpg.add_text("SCALE " + str(round(gameScale, 2)) + "x")
        robotCoordTag = dpg.add_text("ROBOT: X 0 Y 0")
        mouseCoordTag = dpg.add_text("GOAL: X 0 Y 0")

    def clicked(num):
        def handleClick():
            dpg.set_value("checkbox1", num == 1)
            dpg.set_value("checkbox2", num == 2)
            dpg.set_value("checkbox3", num == 3)
            dpg.set_value("checkbox4", num == 4)
            dpg.set_value("checkbox5", num == 5)
        return handleClick
    # create window for control buttons and stuff
    with dpg.window(tag="ctlwindow2", label="", no_close=True, min_size=(450, 250), pos=(SCREENWIDTH / 2 + 20, 250)):
        # Add 5 checkboxes named 1 to 5. If you click on one, then the others will be unchecked. When a checkbox is clicked, set a global variable to the int value of the checkbox.
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label="1", callback=clicked(1), tag="checkbox1")
            dpg.add_checkbox(label="2", callback=clicked(2), tag="checkbox2")
            dpg.add_checkbox(label="3", callback=clicked(3), tag="checkbox3")
            dpg.add_checkbox(label="4", callback=clicked(4), tag="checkbox4")
            dpg.add_checkbox(label="5", callback=clicked(5), tag="checkbox5")

    #show viewport
    dpg.show_viewport()

    #run program
    while dpg.is_dearpygui_running():
        dpg.set_value(fpsTag, updateFps())
        #dpg.set_value(robotCoordTag,"ROBOT: X "+str(robotX)+" Y "+str(1334-robotY))
        
        dpg.render_dearpygui_frame()                      

    dpg.destroy_context()
    os._exit(0)

if __name__ == "__main__":
    main()
