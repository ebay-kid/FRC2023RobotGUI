import ctypes
import os
import time

import dearpygui.dearpygui as dpg
import pyautogui
from PIL import Image

import network_tables
from constants import *
from fps import update_fps
from trajectoryHandler import generateTrajectoryVector
from util import *
from util import meters_to_pixels, flat_img

# initialize user32 to read monitor size
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# some constants
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)

# dynamically updating global variables
trajectoryCoords = np.zeros((500, 500))
latestX = 0
latestY = 0
game_scale = 1

# Global Tags
robotCoordTag = 0
scaleTag = 0
mouseCoordTag = 0

# Connect to NetworkTables
if USING_NETWORK_TABLES and __name__ == "__main__":
    network_tables.init()
    while not network_tables.is_connected():
        time.sleep(0.3)

# Initialize and Values using NetworkTables
teamColor = True  # True = Blue, False = Red
robotX = meters_to_pixels(5.83)
robotY = meters_to_pixels(4.025)
robotAngle = 0

ROBOT_LENGTH_IMG = meters_to_pixels(ROBOT_LENGTH_REAL_M)
ROBOT_HEIGHT_IMG = meters_to_pixels(ROBOT_HEIGHT_REAL_M)


# redraw all elements
def update_graphics():
    trajectory_draw = np.zeros(np.shape(trajectoryCoords))
    background_draw = [0] * 2
    robot_draw = [0] * 2
    for i in range(np.shape(trajectoryCoords)[1]):
        trajectory_draw[0][i], trajectory_draw[1][i] = zoom_coordinate(trajectoryCoords[0][i], trajectoryCoords[1][i],
                                                                       robotX, robotY, game_scale)
    background_draw[0] = zoom_coordinate(0, 0, robotX, robotY, game_scale)
    background_draw[1] = zoom_coordinate(FIELD_WIDTH_IMG, FIELD_HEIGHT_IMG, robotX, robotY, game_scale)
    robot_draw[0] = zoom_coordinate(robotX, robotY, robotX, robotY, game_scale)
    robot_draw[1] = zoom_coordinate(robotX + ROBOT_LENGTH_IMG, robotY + ROBOT_HEIGHT_IMG, robotX, robotY, game_scale)

    dpg.set_item_height("drawlist", FIELD_HEIGHT_IMG)
    dpg.set_item_width("drawlist", FIELD_WIDTH_IMG)
    if dpg.does_alias_exist:
        dpg.delete_item("drawlist", children_only=True)
    dpg.draw_image("game field", background_draw[0], background_draw[1], uv_min=(0, 0), uv_max=(1, 1),
                   parent="drawlist")
    dpg.draw_image("robot texture", robot_draw[0], robot_draw[1], uv_min=(0, 0), uv_max=(1, 1), parent="drawlist")
    for i in range(np.shape(trajectoryCoords)[1] - 1):
        dpg.draw_line((trajectory_draw[0][i], trajectory_draw[1][i]),
                      (trajectory_draw[0][i + 1], trajectory_draw[1][i + 1]), color=(255, 0, 0, 255), thickness=3,
                      parent="drawlist")


# create trajectory
def create_trajectory():
    global intersectCoords
    global trajectoryCoords
    global latestX
    global latestY
    prev_x = latestX
    prev_y = latestY
    latestX, latestY = reverse_zoom(max(pyautogui.position()[0] - 10, 0), max(pyautogui.position()[1] - 25, 0), robotX,
                                    robotY, game_scale)

    if latestX > FIELD_WIDTH_IMG or latestY > FIELD_HEIGHT_IMG:
        latestX = prev_x
        latestY = prev_y
        return

    dpg.set_value(mouseCoordTag, "GOAL: X " + str(latestX) + " Y " + str(latestY))

    if robotY < latestY:
        temp_angle = robotAngle + 90
    else:
        temp_angle = robotAngle - 90
    intersectCoords, trajectoryCoords = generateTrajectoryVector(robotX, robotY, temp_angle, latestX, latestY)
    update_graphics()


def update_click_pos():
    global latestX
    global latestY

    prev_x = latestX
    prev_y = latestY
    latestX, latestY = reverse_zoom(max(pyautogui.position()[0] - 8, 0), max(pyautogui.position()[1] - 8, 0), robotX,
                                    robotY, game_scale)

    if latestX > FIELD_WIDTH_IMG or latestY > FIELD_HEIGHT_IMG:
        latestX = prev_x
        latestY = prev_y
        return
    dpg.set_value(mouseCoordTag, "GOAL: X " + str(latestX) + " Y " + str(latestY))
    update_graphics()


# main APP CONTROL
def main():
    # always create context first
    dpg.create_context()

    # get image and convert to 1D array to turn into a static texture
    img = Image.open(image_path('field_2025_m_rot'))
    robot_img = Image.open(image_path('robot_2025'))
    if teamColor:
        img_rotated = img.rotate(0, expand=True)
    else:
        img_rotated = img.rotate(180, expand=True)

    dpg_image = flat_img(img_rotated)
    dpg_image2 = flat_img(robot_img)
    width2 = robot_img.width
    height2 = robot_img.height
    # load all textures
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=FIELD_WIDTH_IMG, height=FIELD_HEIGHT_IMG, default_value=dpg_image,
                               tag="game field")
        dpg.add_static_texture(width=width2, height=height2, default_value=dpg_image2, tag="robot texture")

    # create viewport
    dpg.create_viewport(title='Team 3952', width=screen_width, height=screen_height)
    dpg.set_viewport_vsync(ENABLE_VSYNC)
    dpg.setup_dearpygui()
    dpg.toggle_viewport_fullscreen()
    dpg.set_global_font_scale(3)

    # mouse wheel scaling
    def scale_image(sender, app_data):
        global game_scale
        game_scale += (app_data * 0.05)
        if game_scale < 1:
            game_scale = 1
        else:
            update_graphics()
        dpg.set_value(scaleTag, "SCALE " + str(round(game_scale, 2)) + "x")

    # basically an event handler
    with dpg.handler_registry():
        # dpg.add_mouse_wheel_handler(callback=scale_image)
        # dpg.add_mouse_click_handler(callback=createTrajectory)
        dpg.add_mouse_click_handler(callback=update_click_pos)

    # create window for drawings and images
    with dpg.window(tag="Window1", no_scroll_with_mouse=True):
        dpg.set_primary_window("Window1", True)
        with dpg.drawlist(tag="drawlist", width=FIELD_WIDTH_IMG, height=FIELD_HEIGHT_IMG, parent="Window1"):
            dpg.draw_image("game field", (0, 0), (FIELD_WIDTH_IMG, FIELD_HEIGHT_IMG), uv_min=(0, 0), uv_max=(1, 1))
            dpg.draw_image("robot texture", (robotX, robotY),
                           (robotX + ROBOT_LENGTH_IMG, robotY + ROBOT_HEIGHT_IMG), uv_min=(0, 0), uv_max=(1, 1))

    # create window for text
    with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(450, 250), pos=(screen_width / 2 + 20, 10)):
        global mouseCoordTag
        global robotCoordTag
        global scaleTag
        fps_tag = dpg.add_text("FPS 0")
        scaleTag = dpg.add_text("SCALE " + str(round(game_scale, 2)) + "x")
        robotCoordTag = dpg.add_text("ROBOT: X 0 Y 0")
        mouseCoordTag = dpg.add_text("GOAL: X 0 Y 0")

    def clicked(num):
        def handle_click():
            dpg.set_value("checkbox1", num == 1)
            dpg.set_value("checkbox2", num == 2)
            dpg.set_value("checkbox3", num == 3)
            dpg.set_value("checkbox4", num == 4)
            dpg.set_value("checkbox5", num == 5)

        return handle_click

    # create window for control buttons and stuff
    with dpg.window(tag="ctlwindow2", label="", no_close=True, min_size=(450, 250), pos=(screen_width / 2 + 20, 250)):
        # Add 5 checkboxes named 1 to 5. If you click on one, then the others will be unchecked. When a checkbox is clicked, set a global variable to the int value of the checkbox.
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label="1", callback=clicked(1), tag="checkbox1")
            dpg.add_checkbox(label="2", callback=clicked(2), tag="checkbox2")
            dpg.add_checkbox(label="3", callback=clicked(3), tag="checkbox3")
            dpg.add_checkbox(label="4", callback=clicked(4), tag="checkbox4")
            dpg.add_checkbox(label="5", callback=clicked(5), tag="checkbox5")

    # show viewport
    dpg.show_viewport()

    # run program
    while dpg.is_dearpygui_running():
        dpg.set_value(fps_tag, update_fps())
        dpg.set_value(robotCoordTag, "ROBOT: X " + str(robotX) + " Y " + str(1334 - robotY))

        dpg.render_dearpygui_frame()

    dpg.destroy_context()
    os._exit(0)


if __name__ == "__main__":
    main()
