# yes i know i just called the file keylogger.py
# yes i know how bad that sounds
import threading

from pynput.keyboard import Listener
import network_tables_util
from constants import USING_NETWORK_TABLES

VERBOSE = True

def publish_key_press(char_pressed):
    code_pressed = int(char_pressed)
    if USING_NETWORK_TABLES:
        network_tables_util.get_entry("robogui", "selectedPlacementPosition").setInteger(code_pressed)
    if VERBOSE:
        print(f"Published key '{char_pressed}' ({code_pressed})")

def on_press(key):
    try:
        char_pressed = key.char
    except AttributeError:
        return
    if char_pressed in "123456789":
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