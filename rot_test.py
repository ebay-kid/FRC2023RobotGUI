import dearpygui.dearpygui as dpg
import math

from PIL import Image

from util import image_path, rotate

dpg.create_context()
dpg.create_viewport()
dpg.setup_dearpygui()
width, height, channels, data = dpg.load_image(image_path('robot_2025'))
# robot_img = Image.open(image_path('robot_2025'))
#r  = util.flat_img(robot_img)
with dpg.texture_registry(show=False):
    dpg.add_raw_texture(width, height, data, tag="robo")

with dpg.window(label="a", width=1000, height=1000):
    with dpg.draw_node(tag="r"):
        a = 30.0 * math.pi / 180
        c = math.cos(a)
        s = math.sin(a)
        w2 = 300 / 2
        h2 = 300 / 2
        dpg.draw_image_quad("robo", rotate((-w2, -h2), c, s), rotate((w2, -h2), c, s), rotate((w2, h2), c, s), rotate((-w2, h2), c, s))
            # dpg.draw_rectangle((0,0), (100, 100), color=(0, 255,0))
# dpg.apply_transform("ar", dpg.create_translation_matrix((300, 300)))
a = dpg.create_rotation_matrix(math.pi * .25, [0, 0, -1])
b = dpg.create_translation_matrix((200, 200))
# dpg.apply_transform("r", a*b)
dpg.show_viewport()
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()

dpg.destroy_context()