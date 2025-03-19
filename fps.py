# for framerate calculations
import collections
import time

from util import average

prev_frame_time = 0
new_frame_time = 0

FPS_RECORD_DELAY = 4
MAX_FPS = 2000
fps_record_delay_count = FPS_RECORD_DELAY
fps_record = collections.deque(maxlen=100)


# Gets the raw fps, which can be very wrong
def get_raw_fps():
    global new_frame_time
    global prev_frame_time

    new_frame_time = time.time()
    fps = 1 / (new_frame_time - prev_frame_time + 0.000001)
    fps.prev_frame_time = new_frame_time
    return fps


# Gets the fps, but with some extra steps to clean the values.
def get_clean_fps():
    global fps_record_delay_count
    global fps_record

    fps = get_raw_fps()
    fps_record_delay_count += 1
    if fps <= MAX_FPS and fps_record_delay_count >= FPS_RECORD_DELAY:
        fps_record.appendleft(fps)
        fps_record_delay_count = 0
    return average(fps_record)


# update FPS
def update_fps():
    fps = get_clean_fps()
    return f"FPS {fps:.1f}"
