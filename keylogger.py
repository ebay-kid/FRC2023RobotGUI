# yes i know i just called the file keylogger.py
# yes i know how bad that sounds
import threading

import pynput.keyboard
from pynput.keyboard import Listener
import network_tables_util
from constants import USING_NETWORK_TABLES

VERBOSE = True


def get_numlock_state():
    import ctypes
    dll = ctypes.WinDLL("User32.dll")
    vk_numlock = 0x90
    return dll.GetKeyState(vk_numlock) == 1


def map_char_pressed_to_upload_value(char_pressed):
    match char_pressed:
        case '/':
            return 1
        case '7':
            return 2
        case '4':
            return 3
        case '2':
            return 4
        case '6':
            return 5
        case '9':
            return 6
    return -1


def publish_key_press(char_pressed):
    # code_pressed = int(char_pressed)
    print("detected: " + char_pressed)
    upload_code = map_char_pressed_to_upload_value(char_pressed)
    if USING_NETWORK_TABLES:
        network_tables_util.get_entry("robogui", "selectedPlacementPosition").setInteger(upload_code)
    if VERBOSE:
        print(f"Detected key '{char_pressed}' which was mapped to '{upload_code}' for upload")


def on_press(key: pynput.keyboard.Key | pynput.keyboard.KeyCode):
    print(get_numlock_state())
    try:
        print("key", key)
        if 97 <= key.vk <= 105:
            publish_key_press(str(key.vk - 96))
            return
        char_pressed = key.char
    except AttributeError:
        print("attribute error")
        return
    if char_pressed is None:
        print("Null?")
        return
    if char_pressed in "123456789/":
        publish_key_press(char_pressed)


def on_release(key):
    if key == 'esc':  # If 'Esc' is released, stop the listener
        print("Escape key released. Exiting...")
        # return False  # Stop the listener


def attach_listener():
    t = threading.Thread(target=attach_listener_internal)
    t.start()
    # attach_listener_internal()


def attach_listener_internal():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
        # pass


if __name__ == "__main__":
    attach_listener()
