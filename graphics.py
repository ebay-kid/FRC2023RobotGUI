import threading
from networktables import NetworkTables
import dearpygui.dearpygui as dpg
import time 
import numpy as np
from PIL import Image
import ctypes
from trajectoryHandler import generateTrajectoryVector
import pyautogui


usingNetworkTables = False #am i using network tables

#for framerate calculations
prev_frame_time = 0
new_frame_time = 0
gameScale = 1
latestX = 0
latestY = 0
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
screenWidth = user32.GetSystemMetrics(0)
screenHeight = user32.GetSystemMetrics(1)


if(usingNetworkTables):
    cond = threading.Condition()
    notified = [False]

    def connectionListener(connected, info):
        print(info, '; Connected=%s' % connected)
        with cond:
            notified[0] = True
            cond.notify()

    NetworkTables.initialize(server='10.39.52.2')
    NetworkTables.addConnectionListener(connectionListener, immediateNotify=True)

    with cond:
        print("Waiting")
        if not notified[0]:
            cond.wait()

    # Insert your processing code here
    print("Connected!")

#Initialize Values using NetworkTables
teamColor = False #True = Blue, False = Red
robotX = 400
robotY = 500

def updateFps():
    global new_frame_time
    global prev_frame_time
    new_frame_time = time.time()
    fps = 1/(new_frame_time-prev_frame_time+0.000001)
    prev_frame_time = new_frame_time
    return "FPS " + str(int(fps))

def flat_img(mat):
    mat.putalpha(255)
    dpg_image = np.frombuffer(mat.tobytes(), dtype=np.uint8) / 255.0
    return dpg_image

def zoom_image(width,height,zoomX,zoomY,factor):
    scalechange = factor - 1;
    invertFactor = 2 - factor;
    offsetX = -(zoomX * scalechange);
    offsetY = -(zoomY * scalechange);
    adjustedWidth = width * factor
    adjustedHeight = height * factor

    dpg.set_item_height("drawlist", height)
    dpg.set_item_width("drawlist", screenWidth/3)
    if dpg.does_alias_exist:
        dpg.delete_item("drawlist", children_only=True)
    dpg.draw_image("game field", (offsetX, offsetY), (offsetX+adjustedWidth, offsetY+adjustedHeight), uv_min=(0, 0), uv_max=(1,1), parent="drawlist")
    dpg.draw_image("robot texture", ((robotX-64)*(1-scalechange/2), (robotY-64)*(1-scalechange/2)), ((robotX+64)*(1+scalechange/2), (robotY+64)*(1+scalechange/2)), uv_min=(0, 0), uv_max=(1, 1), parent="drawlist")
    print(adjustedWidth,adjustedHeight)

def createTrajectory():
    global latestX
    global latestY
    latestX = max(pyautogui.position()[0] - 7,0)
    latestY = max(1334 - pyautogui.position()[1],0)
    generateTrajectoryVector(robotX,robotY,latestX,latestY)

def main():

    #always create context first
    dpg.create_context()
    
    #get image and convert to 1D array to turn into a static texture
    img = Image.open('gamefield.png')
    robotImg = Image.open('notRobot.png')
    if teamColor:
        img_rotated = img.rotate(90, expand=True)
    else:
        img_rotated = img.rotate(-90, expand=True)
        
    dpg_image = flat_img(img_rotated)
    dpg_image2 = flat_img(robotImg)
    width = img_rotated.width;
    height = img_rotated.height;
    width2 = robotImg.width;
    height2 = robotImg.height;

    #load all textures
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=width, height=height, default_value=dpg_image, tag="game field")
        dpg.add_static_texture(width=width2, height=height2, default_value=dpg_image2, tag="robot texture")

    #create viewport
    dpg.create_viewport(title='Team 3952', width=screenWidth, height=screenHeight)
    #dpg.set_viewport_vsync(False)
    dpg.setup_dearpygui()
    dpg.toggle_viewport_fullscreen()
    dpg.set_global_font_scale(3)

    #mouse wheel scaling
    def scale_image(sender, app_data):
        global gameScale
        gameScale += (app_data*0.05)
        if gameScale < 1.0:
            gameScale = 1.0
        else:
            zoom_image(width,height,robotX,robotY,gameScale)
    with dpg.handler_registry():
        dpg.add_mouse_wheel_handler(callback=scale_image)
        dpg.add_mouse_click_handler(callback=createTrajectory)
    
    #create window
    with dpg.window(tag="Window1"):
        dpg.set_primary_window("Window1", True)
        with dpg.drawlist(tag="drawlist", width=screenWidth/3, height=height, parent="Window1"):
            dpg.draw_image("game field", (0, 0), (width, height), uv_min=(0, 0), uv_max=(1, 1))
            dpg.draw_image("robot texture", (robotX-64, robotY-64), (robotX+64, robotY+64), uv_min=(0, 0), uv_max=(1, 1))

    with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(450,250), pos=(screenWidth/3+20,10)):
        fpsTag = dpg.add_text("FPS 0")
        scaleTag = dpg.add_text("SCALE 1x")
        robotCoordTag = dpg.add_text("ROBOT: X 0 Y 0")
        mouseCoordTag = dpg.add_text("GOAL: X 0 Y 0")


    #show viewport
    dpg.show_viewport()

    scale = 1

    #run program
    while dpg.is_dearpygui_running():
        dpg.set_value(fpsTag,updateFps())
        dpg.set_value(scaleTag,"SCALE " + str(round(gameScale,2)) + "x")
        dpg.set_value(robotCoordTag,"ROBOT: X "+str(robotX)+" Y "+str(robotY))
        dpg.set_value(mouseCoordTag,"GOAL: X "+str(latestX)+" Y "+str(latestY))
        dpg.render_dearpygui_frame()                      

    dpg.destroy_context()

main()