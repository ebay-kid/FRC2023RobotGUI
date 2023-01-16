import threading
from networktables import NetworkTables
import dearpygui.dearpygui as dpg
import time 
import numpy as np
from PIL import Image
import ctypes
from trajectoryHandler import generateTrajectoryVector
import pyautogui

#intialize user32 to read monitor size
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

#for framerate calculations
prev_frame_time = 0
new_frame_time = 0

#Constants
ENABLEVSYNC = True
USINGNETWORKTABLES = False
SCREENWIDTH = user32.GetSystemMetrics(0)
SCREENHEIGHT = user32.GetSystemMetrics(1)
ROBOTLENGTH = 64
ROBOTHEIGHT = 64
FIELDWIDTH = 660
FIELDHEIGHT = 1305

#dynamically updating global variables
trajectoryCoords = []
latestX = 0
latestY = 0
gameScale = 1

#draw coordinate global variables
tDraw = [] #trajectories
bDraw = [0] * 2 #background
rDraw = [0] * 2 #robot

#Connect to NetworkTables
if USINGNETWORKTABLES:
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

#Initialize and Values using NetworkTables
teamColor = False #True = Blue, False = Red
robotX = 200
robotY = 200
robotAngle = 0

#update FPS
def updateFps():
    global new_frame_time
    global prev_frame_time
    new_frame_time = time.time()
    fps = 1/(new_frame_time-prev_frame_time+0.000001)
    prev_frame_time = new_frame_time
    return "FPS " + str(int(fps))

#flatten image to be used as Texture
def flat_img(mat):
    mat.putalpha(255)
    dpg_image = np.frombuffer(mat.tobytes(), dtype=np.uint8) / 255.0
    return dpg_image

#redraw all elements
def update_graphics():
    tDraw = np.zeros(np.shape(trajectoryCoords))
    for i in range(np.shape(trajectoryCoords)[1]):
        tDraw[0][i],tDraw[1][i] = zoom_coordinate(trajectoryCoords[0][i],trajectoryCoords[1][i],robotX,robotY,gameScale)
    bDraw[0] = zoom_coordinate(0,0,robotX,robotY,gameScale)
    bDraw[1] = zoom_coordinate(FIELDWIDTH,FIELDHEIGHT,robotX,robotY,gameScale)
    rDraw[0] = zoom_coordinate(robotX-ROBOTLENGTH,robotY-ROBOTHEIGHT,robotX,robotY,gameScale)
    rDraw[1] = zoom_coordinate(robotX+ROBOTLENGTH,robotY+ROBOTHEIGHT,robotX,robotY,gameScale)

    dpg.set_item_height("drawlist", FIELDHEIGHT)
    dpg.set_item_width("drawlist", SCREENWIDTH/3)
    if dpg.does_alias_exist:
        dpg.delete_item("drawlist", children_only=True)
    dpg.draw_image("game field", bDraw[0], bDraw[1], uv_min=(0, 0), uv_max=(1,1), parent="drawlist")
    dpg.draw_image("robot texture", rDraw[0], rDraw[1], uv_min=(0, 0), uv_max=(1, 1), parent="drawlist")
    for i in range(np.shape(trajectoryCoords)[1]-1):
        dpg.draw_line((tDraw[0][i],tDraw[1][i]), (tDraw[0][i+1], tDraw[1][i+1]), color=(255, 0, 0, 255), thickness=3, parent="drawlist")

#apply zoom to coordinate
def zoom_coordinate(x,y,zoomX,zoomY,factor):
    return x,y

#create trajectory
def createTrajectory():
    global trajectoryCoords
    global latestX
    global latestY
    latestX = max(pyautogui.position()[0],0)
    latestY = max(pyautogui.position()[1],0)
    if(robotY < latestY):
        tempAngle = robotAngle+90
    else:
        tempAngle = robotAngle-90
    trajectoryCoords = generateTrajectoryVector(robotX,robotY,tempAngle,latestX,latestY,0)
    update_graphics()

#main APP CONTROL
def main():

    #always create context first
    dpg.create_context()
    
    #get image and convert to 1D array to turn into a static texture
    img = Image.open('gamefield.png')
    robotImg = Image.open('robot.png')
    if teamColor:
        img_rotated = img.rotate(90, expand=True)
    else:
        img_rotated = img.rotate(-90, expand=True)
        
    dpg_image = flat_img(img_rotated)
    dpg_image2 = flat_img(robotImg)
    width2 = robotImg.width;
    height2 = robotImg.height;

    #load all textures
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=FIELDWIDTH, height=FIELDHEIGHT, default_value=dpg_image, tag="game field")
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
        gameScale += (app_data*0.05)
        if gameScale < 1.0:
            gameScale = 1.0
        else:
            update_graphics()

    #basically an event handler
    with dpg.handler_registry():
        dpg.add_mouse_wheel_handler(callback=scale_image)
        dpg.add_mouse_click_handler(callback=createTrajectory)
    
    #create window for drawings and images
    with dpg.window(tag="Window1"):
        dpg.set_primary_window("Window1", True)
        with dpg.drawlist(tag="drawlist", width=SCREENWIDTH/3, height=FIELDHEIGHT, parent="Window1"):
            dpg.draw_image("game field", (0, 0), (FIELDWIDTH, FIELDHEIGHT), uv_min=(0, 0), uv_max=(1, 1))
            dpg.draw_image("robot texture", (robotX-64, robotY-64), (robotX+64, robotY+64), uv_min=(0, 0), uv_max=(1, 1))

    #create window for text 
    with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(450,250), pos=(SCREENWIDTH/3+20,10)):
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
        dpg.set_value(robotCoordTag,"ROBOT: X "+str(robotX)+" Y "+str(1334-robotY))
        dpg.set_value(mouseCoordTag,"GOAL: X "+str(latestX)+" Y "+str(1334-latestY))
        dpg.render_dearpygui_frame()                      

    dpg.destroy_context()

main()