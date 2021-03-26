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
        set_emitters(set == 'on')
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
    global cam, debug_opencv, stream
    # Start IR emitter
    LampState('on')
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
    try:
        while LampState():
            FindNewPoints()
    finally:
        End()


def IsGesture(newA, newB, oldA, oldB, i):
    """
    Determines if the point has moved.
    """
    global ig
    print("point: %s" % i)
    #look for basic movements - TODO: trained gestures
    if ((newA<(oldA-5))&(abs(newB-oldB)<1)):
        ig[i].append("left")
    elif ((oldA<(newA-5))&(abs(newB-oldB)<1)):
        ig[i].append("right")
    elif ((newB<(oldB-5))&(abs(newA-oldA)<5)):
        ig[i].append("up")
    elif ((oldB<(newB-5))&(abs(newA-oldA)<5)):
        ig[i].append("down")
    #check for gesture patterns in array
    astr = ''.join(map(str, ig[i]))
    print(f'Spell string: {astr}')
    if "rightup" in astr:
        cast_spell('lumos')
    elif "rightdown" in astr:
        cast_spell('nox')
    elif "leftdown" in astr:
        cast_spell('colovaria')
    elif "leftup" in astr:
        cast_spell('incendio')


def FindNewPoints():
    """
    FindWand is called to find all potential wands in a scene.  These are then 
    tracked as points for movement.  The scene is reset every 3 seconds.
    """
    global old_frame, \
           old_gray, \
           p0, \
           mask, \
           color, \
           ig, \
           img, \
           frame, \
           cam
    try:
        while LampState():
            try:
                old_frame = cam.capture(stream, format='jpeg')
            except:
                print("resetting points")
            data = np.fromstring(stream.getvalue(), dtype=np.uint8)
            old_frame = cv2.imdecode(data, 1)
            cv2.flip(old_frame,1,old_frame)
            old_gray = cv2.cvtColor(old_frame,cv2.COLOR_BGR2GRAY)

            #TODO: trained image recognition
            p0 = cv2.HoughCircles(old_gray,
                                cv2.HOUGH_GRADIENT,
                                3,
                                100,
                                param1=100,
                                param2=30,
                                minRadius=4,
                                maxRadius=15)
            if p0 is not None:
                p0.shape = (p0.shape[1], 1, p0.shape[2])
                p0 = p0[:,:,0:2]
                mask = np.zeros_like(old_frame)
                ig = [[0] for x in range(20)]
                print("Run TrackWand")
                TrackWand()

    except Exception as e:
        print(f'Error: {e}')
        End()
        exit


def TrackWand():
    """
    Tracks wand points for 3 seconds.
    """
    global old_frame, \
           old_gray, \
           p0, \
           mask, \
           color, \
           ig, \
           img, \
           frame
    color = (0,0,255)
    try:
        old_frame = cam.capture(stream, format='jpeg')
    except:
        print("resetting points")
    data = np.fromstring(stream.getvalue(), dtype=np.uint8)
    old_frame = cv2.imdecode(data, 1)
    cv2.flip(old_frame,1,old_frame)
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    # Take first frame and find circles in it
    p0 = cv2.HoughCircles(old_gray,
                          cv2.HOUGH_GRADIENT,
                          3,
                          100,
                          param1=100,
                          param2=30,
                          minRadius=4,
                          maxRadius=15)
    try:
        p0.shape = (p0.shape[1], 1, p0.shape[2])
        p0 = p0[:,:,0:2]
    except:
        print("No points found")
	# Create a mask image for drawing purposes
    mask = np.zeros_like(old_frame)

    timer = time.time()

    # Run for 3 seconds and reset
    while LampState() and (time.time() - timer) < 3:
        frame = cam.capture(stream, format='jpeg')
        data2 = np.fromstring(stream.getvalue(), dtype=np.uint8)
        frame = cv2.imdecode(data2, 1)
        cv2.flip(frame,1,frame)
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        try:
            # calculate optical flow
            p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
            # Select good points
            good_new = p1[st==1]
            good_old = p0[st==1]
            print('start looking for points')
            # draw the tracks
            for i,(new,old) in enumerate(zip(good_new,good_old)):
                newA, newB = new.ravel()
                oldA, oldB = old.ravel()
                # only try to detect gesture on highly-rated points (below 15)
                print('is there a gesture?')
                if (i<15):
                    print('yes!')
                    IsGesture(newA, newB, oldA, oldB, i)
                    dist = math.hypot(newA - oldA, newB - oldB)
                    print(f'dist: {dist}')
                    if (dist<movment_threshold):
                        cv2.line(mask, (newA, newB),(oldA, oldB),(0,255,0), 2)
                        cv2.circle(frame,(newA, newB),5,color,-1)
                        cv2.putText(frame,
                                    str(i),
                                    (newA, newB),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    1.0,
                                    (0,0,255))
        except IndexError:
            print("Index error")
            End()
            break
        except:
            e = sys.exc_info()[0]
            print(f'TrackWand Error: {e}')
            # End()
            break
        img = cv2.add(frame,mask)
        # save for debug
        cv2.imwrite('test.jpg', frame_gray)

        if debug_opencv:
            cv2.putText(img,
                        "Press ESC to close.",
                        (5, 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0,
                        (255,255,255))
            cv2.imshow("Raspberry Potter", frame)

        # get next frame
        frame = cam.capture(stream, format='jpeg')
        data3 = np.fromstring(stream.getvalue(), dtype=np.uint8)
        frame = cv2.imdecode(data3, 1)

        # Now update the previous frame and previous points
        old_gray = frame_gray.copy()
        p0 = good_new.reshape(-1,1,2)


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

def End():
    global cam
    # Stop IR emitter
    LampState('off')
    print('=== END ===')
    if cam:
	    cam.close()
    cv2.destroyAllWindows()

def WatchSpellsOn():
    """Start watching for spells."""
    LampState('on')
    # Light up for 5s to let the Wizard know you're ready
    lumos(0)
    # start capturing
    StartCamera()
    # track wand
    # print("Begin Tracking Wand")
    # TrackMotion()

def WatchSpellsOff():
    """Stop watching for spells."""
    LampState('off')
    End()
    # Light up for 5s to let the Wizard know you're done
    lumos(0, (127, 10, 10))
