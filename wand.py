"""
Identify spells cast by the user.
"""

"""
Code based on https://github.com/sean-obrien/rpotter

  _\
  \
O O-O
 O O
  O
  
Raspberry Potter
Ollivander - Version 0.2 

Use your own wand or your interactive Harry Potter wands to control the IoT.

Copyright (c) 2016 Sean O'Brien.  Permission is hereby granted, free of charge,
to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom
the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import io
import numpy as np
import cv2
import picamera
import threading
import sys
import math
import time
import warnings
import redis
from PIL import Image
from config import potter_lamp_config as config
from spells import cast_spell, lumos
from emitters import set_emitters

# Set global variables
debug_opencv = config["debug_opencv"]
cam = None
stream = io.BytesIO()

# Use redis to track state of lamp
redis_ns = config["redis_namespace"]
store = redis.Redis() # defaults for localhost will work just fine

def LampState(set=None):
    """Retrieve or set lamp state."""
    if set in ['on', 'off']:
        store.set(f'{redis_ns}:potter_lamp', set)
    return store.get(f'{redis_ns}:potter_lamp').decode('utf-8') == 'on'

# Set default lamp state
LampState('off')

# OpenCV Parameters for image processing
lk_params = dict( winSize  = (15,15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
dilation_params = (5, 5)
movment_threshold = 80

def StartCamera():
    """Initialize camera input."""
    global cam
    global debug_opencv
    # Start IR emitter
    set_emitters(True)
    # Open a window for debug
    if debug_opencv:
        cv2.namedWindow("Raspberry Potter")
    # Initialize camera
    try:
        cam = picamera.PiCamera()
    except Exception as camera:
        print('Camera already open')
    cam.resolution = (640, 480)
    cam.framerate = 24

def CaptureStill():
    """Capture still image to analyze."""
    # Grab image
    frame = cam.capture(stream, format='jpeg')

    # Isolate reflective tip
    stream.seek(0)
    data2 = np.fromstring(stream.getvalue(), dtype=np.uint8)
    frame = cv2.imdecode(data2, 1)
    # cv2.flip(frame,1,frame)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # save for debug
    # image = Image.open(stream)
    # image.save('test.jpg', 'jpeg')
    cv2.imwrite('test.jpg', frame)

    # just once for now
    WatchSpellsOff()
    return frame

def TrackMotion():
    """Compare images for motion."""
    print('start tracking')
    while LampState():
        frame = CaptureStill()
        print('image saved?')
        if frame is None:
            break
        
    pass

#
##TODO: Turn off spells after no spells have been cast within a
#       specified timeframe defined in config.

def End():
    # Stop IR emitter
    set_emitters(False)
    if cam:
	    cam.close()
    if cv2:
	    cv2.destroyAllWindows()

def WatchSpellsOn():
    """Start watching for spells."""
    LampState('on')
    # Light up for 5s to let the Wizard know you're ready
    # lumos(0)
    # start capturing
    StartCamera()
    # track wand
    print("Begin Tracking Wand")
    TrackMotion()

def WatchSpellsOff():
    """Stop watching for spells."""
    LampState('off')
    End()
