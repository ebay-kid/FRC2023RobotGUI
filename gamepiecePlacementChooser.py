import dearpygui.dearpygui as dpg
import time
import numpy as np
import network_tables
import os
import ctypes
from PIL import Image

# some constants
SCREENWIDTH = ctypes.windll.user32.GetSystemMetrics(0)
SCREENHEIGHT = ctypes.windll.user32.GetSystemMetrics(1)

ENTIRE_OFFSET = np.array((0, 0))

USINGNETWORKTABLES = False

INITIAL_OFFSET = np.array((30, 8))

THREE_X_THREE_OFFSETS = [
    [np.array((0, 0)),   np.array((100, 0)),   np.array((200, 0))  ],
    [np.array((0, 100)), np.array((100, 100)), np.array((200, 100))],
    [np.array((0, 200)), np.array((100, 200)), np.array((200, 200))]
]

THREE_X_THREE_OUTER_OFFSETS = [
    np.array((0, 0)), np.array((300, 0)), np.array((600, 0))
]

KEYBINDS = \
    "qwertyuio" + \
    "asdfghjkl" + \
    "zxcvbnm¼¾" # 1/4, 3/4 actually means comma and period. why? no clue blame python chr()

POSITIONS = [None] * len(KEYBINDS)

#Connect to NetworkTables
if USINGNETWORKTABLES and __name__ == "__main__":
    network_tables.init()
    while not network_tables.isConnected():
        time.sleep(0.3)

def flat_img(mat):
    mat.putalpha(255)
    dpg_image = np.frombuffer(mat.tobytes(), dtype=np.uint8) / 255.0
    return dpg_image

currentlySelected = -1

def fixText(text: str):
    if text == "¾":
        return "."
    elif text == "¼":
        return ","
    return text.capitalize()

SCALE_LETTERS = 69

def onKeyPress(sender, app_data):
    global currentlySelected
    
    pressed = chr(app_data).lower()
    idx = KEYBINDS.find(pressed)
    if idx == -1 or idx == currentlySelected:
        return
    dpg.delete_item(str(idx))

    dpg.draw_text(pos=POSITIONS[idx], text=fixText(KEYBINDS[idx]), show=True, size=SCALE_LETTERS, color=(0, 255, 0, 255), label=idx, parent="drawlist")
    if currentlySelected != -1:
        dpg.delete_item(str(currentlySelected))
        dpg.draw_text(pos=POSITIONS[currentlySelected], text=fixText(KEYBINDS[currentlySelected]), show=True, size=SCALE_LETTERS, color=(255, 0, 0, 255), label=currentlySelected, parent="drawlist")
    currentlySelected = idx

    if USINGNETWORKTABLES:
        network_tables.getEntry("robogui", "selectedPlacementPosition").setInteger(currentlySelected)

def main():
    dpg.create_context()

    img = Image.open("assets/placementHUD2.png")
    width = img.width
    height = img.height
    img = flat_img(img)
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=width, height=height, default_value=img, tag="hud")

    #create viewport
    dpg.create_viewport(title='Team 3952', width=SCREENWIDTH, height=SCREENHEIGHT)
    dpg.set_viewport_vsync(True)
    dpg.setup_dearpygui()
    # dpg.toggle_viewport_fullscreen()
    dpg.set_global_font_scale(3)

    with dpg.handler_registry():
        dpg.add_key_press_handler(callback=onKeyPress)

    with dpg.window(tag="MainWindow"):
        dpg.set_primary_window("MainWindow", True)
        with dpg.drawlist(tag="drawlist", width=SCREENWIDTH, height=SCREENHEIGHT, parent="MainWindow"):
            dpg.draw_image("hud", np.array((0, 0)) + ENTIRE_OFFSET, (width, height) + ENTIRE_OFFSET, uv_min=(0, 0), uv_max=(1, 1))
            for i, TxT_outer in enumerate(THREE_X_THREE_OUTER_OFFSETS):
                for j, TxT_inner1 in enumerate(THREE_X_THREE_OFFSETS):
                    for k, TxT_inner2 in enumerate(TxT_inner1):
                        p = TxT_inner2 + TxT_outer + INITIAL_OFFSET + ENTIRE_OFFSET
                        idx = 3 * i + 9 * j + k
                        POSITIONS[idx] = p
                        dpg.draw_text(pos=p, text=fixText(KEYBINDS[idx]), show=True, size=SCALE_LETTERS, color=(255, 0, 0, 255), label=str(idx))

    dpg.show_viewport()
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
    dpg.destroy_context()
    os._exit(0)
if __name__ == "__main__":
    main()