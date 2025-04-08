import ctypes
import os
import time

import dearpygui.dearpygui as dpg
import pyautogui
from PIL import Image

import field_ref
import network_tables_util
import keylogger
from constants import *
from fps import update_fps
from util import *
from util import meters_to_pixels, flat_img

# initialize user32 to read monitor size
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# some constants
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)

# dynamically updating global variables
trajectories: list[field_ref.Trajectory] = []
latest_x = 0
latest_y = 0
game_scale = 1

# Global Tags
robot_coord_tag = 0
scale_tag = 0
mouse_coord_tag = 0
numlock_enabled_tag = 0

# Initialize and Values using NetworkTables
team_color = True  # True = Blue, False = Red
real_robot: field_ref.Robot = field_ref.Robot(5.83, 4.025, 0, 255)
robot_angle = 0

ROBOT_LENGTH_IMG = meters_to_pixels(ROBOT_LENGTH_REAL_M)
ROBOT_HEIGHT_IMG = meters_to_pixels(ROBOT_HEIGHT_REAL_M)

should_update_graphics: bool = False


def queue_graphics_update():
    global should_update_graphics
    should_update_graphics = True


# redraw all elements
def update_graphics():
    global should_update_graphics

    dpg.set_item_height("drawlist", FIELD_HEIGHT_IMG)
    dpg.set_item_width("drawlist", FIELD_WIDTH_IMG)
    if dpg.does_alias_exist("drawlist"):
        dpg.delete_item("drawlist", children_only=True)

    draw_background()
    draw_robot(real_robot)

    for trajectory in trajectories:
        draw_trajectory(trajectory)

    should_update_graphics = False


def draw_robot(robot: field_ref.Robot):
    robot_coords = field_ref.field_to_screen(robot.x, robot.y)
    angle = (90 - robot.rot) * math.pi / 180.0
    cos = math.cos(angle)
    sin = math.sin(angle)
    width2 = ROBOT_LENGTH_IMG / 2.0
    height2 = ROBOT_HEIGHT_IMG / 2.0
    center = np.array(robot_coords)
    # print(cos, sin)
    p1 = center + rotate((-width2, -height2), cos, sin)
    p2 = center + rotate((width2, -height2), cos, sin)
    p3 = center + rotate((width2, height2), cos, sin)
    p4 = center + rotate((-width2, height2), cos, sin)
    # print(p1, p2, p3, p4)
    # print(distance(*p1, *p2), distance(*p2, *p3), distance(*p1, *p4), distance(*p3, *p4))

    dpg.draw_image_quad("robot_image",
                        p1,
                        p2,
                        p3,
                        p4,
                        uv1=(0, 0),
                        uv2=(1, 0),
                        uv3=(1, 1),
                        uv4=(0, 1),
                        parent="drawlist",
                        color=(255, 255, 255, robot.opacity))
    # dpg.draw_quad(p1, p2, p3, p4, tag="q", parent="r", color=(0,255,0,255))
    # dpg.apply_transform("r", dpg.create_translation_matrix(robot_coords))


def draw_background():
    background_draw = [0] * 2
    background_draw[0] = 0, 0
    background_draw[1] = FIELD_WIDTH_IMG, FIELD_HEIGHT_IMG
    dpg.draw_image("game field", background_draw[0], background_draw[1], uv_min=(0, 0), uv_max=(1, 1),
                   parent="drawlist")


def draw_trajectory(traj: field_ref.Trajectory):
    # print(len(traj_coords))
    traj_coords = traj.points
    t_coords = np.zeros((int(len(traj_coords) / 3), 3), dtype=np.float16)
    # print(np.shape(t_coords))
    count = 0
    subcount = 0
    for x in traj_coords:
        t_coords[count][subcount] = x
        subcount += 1
        if subcount == 3:
            subcount = 0
            count += 1

    # print(t_coords)

    for i in range(np.shape(t_coords)[0] - 1):
        dpg.draw_line(field_ref.field_to_screen(t_coords[i][0], t_coords[i][1]),
                      field_ref.field_to_screen(t_coords[i + 1][0], t_coords[i + 1][1]), color=traj.color,
                      thickness=3,
                      parent="drawlist")
        if i % 10 == 0:
            draw_robot(field_ref.Robot(*t_coords[i], 128))
    if np.shape(t_coords)[0] > 0:
        draw_robot(field_ref.Robot(*t_coords[np.shape(t_coords)[0] - 1], 128))


def update_click_pos():
    global latest_x
    global latest_y

    prev_x = latest_x
    prev_y = latest_y
    latest_x, latest_y = reverse_zoom(max(pyautogui.position()[0] - 8, 0), max(pyautogui.position()[1] - 8, 0),
                                      real_robot.x,
                                      real_robot.y, game_scale)

    if latest_x > FIELD_WIDTH_IMG or latest_y > FIELD_HEIGHT_IMG:
        latest_x = prev_x
        latest_y = prev_y
        return
    # dpg.set_value(mouse_coord_tag, "GOAL: X " + str(latest_x) + " Y " + str(latest_y))
    queue_graphics_update()


def update_numlock_text():
    numlock_state = keylogger.get_numlock_state()
    dpg.set_value(numlock_enabled_tag,
                  "Numlock good? " + str(numlock_state) + (" IT IS BAD PLEASE FIX" if not numlock_state else ""))


def update_nt_values():
    if USING_NETWORK_TABLES and network_tables_util.is_connected():
        global real_robot, trajectories

        raw_pose = network_tables_util.get_entry("robot", "raw_pose").getDoubleArray(None)

        if raw_pose:
            real_robot.x, real_robot.y = raw_pose[0], raw_pose[1]
            real_robot.rot = raw_pose[2]
            queue_graphics_update()

        traj_chosen_path: field_ref.Trajectory = field_ref.Trajectory(
            network_tables_util.get_entry("robot", "chosen_path").getDoubleArray([]), (255, 0, 0, 255))
        traj_pathfinder: field_ref.Trajectory = field_ref.Trajectory(
            network_tables_util.get_entry("robot", "pathfinder").getDoubleArray([]), (0, 255, 0, 255))
        traj_connector: field_ref.Trajectory = field_ref.Trajectory(
            network_tables_util.get_entry("robot", "connection_path").getDoubleArray([]), (0, 0, 255, 255))

        trajectories = [traj_chosen_path, traj_pathfinder, traj_connector]


last_nt_update = 0
last_graphics_update_check = 0


# main APP CONTROL
def main():
    # always create context first
    dpg.create_context()

    # get image and convert to 1D array to turn into a static texture
    img = Image.open(image_path('field_2025_m_rot'))
    robot_img = Image.open(image_path('robot_2025'))
    # w, h, c, d = dpg.load_image(image_path('big_robot_2025'))
    if team_color:
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
        dpg.add_static_texture(width=width2, height=height2, default_value=dpg_image2, tag="robot_image")
        # dpg.add_static_texture(w, h, d, tag="robot_image")
    # create viewport
    dpg.create_viewport(title='Team 3952', width=int(screen_width * 1), height=int(screen_height * 0.7))
    dpg.set_viewport_pos((0, 0))
    dpg.set_viewport_vsync(ENABLE_VSYNC)
    dpg.setup_dearpygui()
    # dpg.toggle_viewport_fullscreen()
    dpg.set_global_font_scale(3)

    # mouse wheel scaling
    def scale_image(sender, app_data):
        global game_scale
        game_scale += (app_data * 0.05)
        if game_scale < 1:
            game_scale = 1
        else:
            queue_graphics_update()
        # dpg.set_value(scale_tag, "SCALE " + str(round(game_scale, 2)) + "x")

    # basically an event handler
    with dpg.handler_registry():
        # dpg.add_mouse_wheel_handler(callback=scale_image)
        # dpg.add_mouse_click_handler(callback=createTrajectory)
        dpg.add_mouse_click_handler(callback=update_click_pos)

    # create window for drawings and images
    with dpg.window(tag="Window1", no_scroll_with_mouse=True):
        dpg.set_primary_window("Window1", True)
        with dpg.drawlist(tag="drawlist", width=FIELD_WIDTH_IMG, height=FIELD_HEIGHT_IMG, parent="Window1"):
            queue_graphics_update()

    # create window for text
    with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(370, 250), pos=(3 * screen_width / 4 + 65, 10)):
        global mouse_coord_tag
        global robot_coord_tag
        global scale_tag
        global numlock_enabled_tag

        fps_tag = dpg.add_text("FPS 0")
        # scale_tag = dpg.add_text("SCALE " + str(round(game_scale, 2)) + "x")
        # robot_coord_tag = dpg.add_text("ROBOT: X 0 Y 0")
        # mouse_coord_tag = dpg.add_text("GOAL: X 0 Y 0")
        numlock_state = keylogger.get_numlock_state()
        numlock_enabled_tag = dpg.add_text(
            "Numlock good? " + str(numlock_state) + (" IT IS BAD PLEASE FIX" if not numlock_state else ""), wrap=350)

    """
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
    """

    # show viewport
    dpg.show_viewport()

    if USING_NETWORK_TABLES:  # connect to nt
        network_tables_util.init()
        while not network_tables_util.is_connected():
            time.sleep(0.3)
        queue_graphics_update()

    if USING_KEYLOGGER:
        keylogger.attach_listener()

    # run program
    while dpg.is_dearpygui_running():
        global last_nt_update, last_graphics_update_check, should_update_graphics

        dpg.set_value(fps_tag, update_fps())
        robot_pose_field_x, robot_pose_field_y, robot_pose_field_rot = real_robot.x, real_robot.y, real_robot.rot
        """
        dpg.set_value(robot_coord_tag,
                      "ROBOT: X " + str(round(robot_pose_field_x, 2)) + " Y " + str(
                          round(robot_pose_field_y, 2)) + " ROT " + str(
                          round(robot_pose_field_rot, 2)))
                          """
        update_numlock_text()
        current_time = time.time()
        if current_time - last_nt_update > 1 / 20:
            # print("last update", time.time() - last_nt_update)
            update_nt_values()
            last_nt_update = current_time

        if current_time - last_graphics_update_check > 1 / 30 and should_update_graphics:
            update_graphics()
            last_graphics_update_check = current_time

        dpg.render_dearpygui_frame()

    dpg.destroy_context()
    os._exit(0)


if __name__ == "__main__":
    main()
