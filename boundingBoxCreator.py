import numpy as np
import dearpygui.dearpygui as dpg
import time
from PIL import Image
import pyautogui
import ctypes

from util import image_path

# intialize user32 to read monitor size
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# for framerate calculations
prev_frame_time = 0
new_frame_time = 0

# Constants
ENABLEVSYNC = True
SCREENWIDTH = user32.GetSystemMetrics(0)
SCREENHEIGHT = user32.GetSystemMetrics(1)
FIELDWIDTH = 660
FIELDHEIGHT = 1305

# Global Tags
mouseCoordTag = 0

# dynamically updating global variables
trajectoryCoords = np.zeros((500, 500))
latestX = 0
latestY = 0
game_scale = 1

# draw coordinate global variables
tDraw = []  # trajectories
bDraw = [0] * 2  # background
rDraw = [0] * 2  # robot
intersectCoord = (0, 0)


# update FPS
def updateFps():
    global new_frame_time
    global prev_frame_time
    new_frame_time = time.time()
    fps = 1 / (new_frame_time - prev_frame_time + 0.000001)
    prev_frame_time = new_frame_time
    return "FPS " + str(int(fps))


# flatten image to be used as Texture
def flat_img(mat):
    mat.putalpha(255)
    dpg_image = np.frombuffer(mat.tobytes(), dtype=np.uint8) / 255.0
    return dpg_image


# redraw all elements
def update_graphics():
    dpg.set_item_height("drawlist", FIELDHEIGHT)
    dpg.set_item_width("drawlist", FIELDWIDTH)
    if dpg.does_alias_exist:
        dpg.delete_item("drawlist", children_only=True)
    dpg.draw_image("game field", (0, 0), (FIELDWIDTH, FIELDHEIGHT), uv_min=(0, 0), uv_max=(1, 1), parent="drawlist")


# create trajectory
def createBoundingPoint():
    global latestX
    global latestY
    latestX = max(pyautogui.position()[0] - 10, 0)
    latestY = max(pyautogui.position()[1] - 25, 0)

    dpg.set_value(mouseCoordTag, "CLICK: X " + str(latestX) + " Y " + str(latestY))
    update_graphics()


# main APP CONTROL
def main():
    # always create context first
    dpg.create_context()

    # get image and convert to 1D array to turn into a static texture
    img = Image.open(image_path('gamefield'))
    img_rotated = img.rotate(-90, expand=True)
    dpg_image = flat_img(img_rotated)

    # load all textures
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=FIELDWIDTH, height=FIELDHEIGHT, default_value=dpg_image, tag="game field")

    # create viewport
    dpg.create_viewport(title='Team 3952', width=SCREENWIDTH, height=SCREENHEIGHT)
    dpg.set_viewport_vsync(ENABLEVSYNC)
    dpg.setup_dearpygui()
    dpg.toggle_viewport_fullscreen()
    dpg.set_global_font_scale(3)

    # basically an event handler
    with dpg.handler_registry():
        dpg.add_mouse_click_handler(callback=createBoundingPoint)

    # create window for drawings and images
    with dpg.window(tag="Window1"):
        dpg.set_primary_window("Window1", True)
        with dpg.drawlist(tag="drawlist", width=SCREENWIDTH / 3, height=FIELDHEIGHT, parent="Window1"):
            dpg.draw_image("game field", (0, 0), (FIELDWIDTH, FIELDHEIGHT), uv_min=(0, 0), uv_max=(1, 1))

    # create window for text
    with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(450, 250), pos=(SCREENWIDTH / 3 + 20, 10)):
        global mouseCoordTag
        fpsTag = dpg.add_text("FPS 0")
        mouseCoordTag = dpg.add_text("CLICKED: X 0 Y 0")

    # show viewport
    dpg.show_viewport()

    # run program
    while dpg.is_dearpygui_running():
        dpg.set_value(fpsTag, updateFps())
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


main()
