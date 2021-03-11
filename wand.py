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
from cv2 import *
import picamera
import threading
import sys
import math
import time
import warnings
import redis
from config import potter_lamp_config as config
from spells import cast_spell, lumos

# Use redis to track state of lamp
redis_ns = config["redis_namespace"]
store = redis.Redis() # defaults for localhost will work just fine
store.set(f'{redis_ns}:potter_lamp', 'off')

# Set global variables
debug_opencv = config["debug_opencv"]
cam = None
stream = io.BytesIO()

# OpenCV Parameters for image processing
lk_params = dict( winSize  = (15,15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
dilation_params = (5, 5)
movment_threshold = 80

# Scan starts camera input and runs FindNewPoints
def Scan():
    if debug_opencv:
        cv2.namedWindow("Raspberry Potter")
    cam = picamera.PiCamera()
    cam.resolution = (640, 480)
    cam.framerate = 24
    try:
        while True:
            FindNewPoints()
    except KeyboardInterrupt:
        End()
        exit

##TODO: Turn off spells after no spells have been cast within a
#       specified timeframe defined in config.

def IsGesture(a,b,c,d,i):
    print("point: %s" % i)
    #look for basic movements - TODO: trained gestures
    if ((a<(c-5))&(abs(b-d)<1)):
        ig[i].append("left")
    elif ((c<(a-5))&(abs(b-d)<1)):
        ig[i].append("right")
    elif ((b<(d-5))&(abs(a-c)<5)):
        ig[i].append("up")
    elif ((d<(b-5))&(abs(a-c)<5)):
        ig[i].append("down")
    #check for gesture patterns in array
    astr = ''.join(map(str, ig[i]))
    if "rightup" in astr:
        cast_spell('lumos')
    elif "rightdown" in astr:
        cast_spell('nox')
    elif "leftdown" in astr:
        cast_spell('colovaria')
    elif "leftup" in astr:
        cast_spell('incendio')
    print(astr)

# FindWand is called to find all potential wands in a scene.  These are then 
# tracked as points for movement.  The scene is reset every 3 seconds.
def FindNewPoints():
    global old_frame,old_gray,p0,mask,color,ig,img,frame
    try:
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
	    # This resets the scene every three seconds
        # Continue if lamp is turned on
        if store.get(f'{redis_ns}:potter_lamp').decode('utf-8') == 'on':
            print("Restarting FindWand")
            threading.Timer(3, FindNewPoints).start()
    except Exception as e:
        print(f'Error: {e}')
        End()
        exit

# def FindWand():
#     global rval,old_frame,old_gray,p0,mask,color,ig,img,frame

#     try:
#         rval, old_frame = cam.read()
#         cv2.flip(old_frame,1,old_frame)
#         old_gray = cv2.cvtColor(old_frame,cv2.COLOR_BGR2GRAY)
#         equalizeHist(old_gray)
#         old_gray = GaussianBlur(old_gray,(9,9),1.5)
#         dilate_kernel = np.ones(dilation_params, np.uint8)
#         old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)
#         clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
#         old_gray = clahe.apply(old_gray)
#         #TODO: trained image recognition
#         p0 = cv2.HoughCircles(old_gray,
#                               cv2.HOUGH_GRADIENT,
#                               3,
#                               50,
#                               param1=240,
#                               param2=8,
#                               minRadius=4,
#                               maxRadius=15)
#         if p0 is not None:
#             p0.shape = (p0.shape[1], 1, p0.shape[2])
#             p0 = p0[:,:,0:2]
#             mask = np.zeros_like(old_frame)
#             ig = [[0] for x in range(20)]
#         # Continue if lamp is turned on
#         if store.get(f'{redis_ns}:potter_lamp').decode('utf-8') == 'on':
#             print("finding...")
#             threading.Timer(3, FindWand).start()
#     except Exception as e:
#         print(f'Error: {e}')
#         exit


def TrackWand():
    global old_frame,old_gray,p0,mask,color,ig,img,frame
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

    while True:
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
            # draw the tracks
            for i,(new,old) in enumerate(zip(good_new,good_old)):
                a,b = new.ravel()
                c,d = old.ravel()
                # only try to detect gesture on highly-rated points (below 15)
                if (i<15):
                    IsGesture(a,b,c,d,i)
                    dist = math.hypot(a - c, b - d)
                    if (dist<movment_threshold):
                        cv2.line(mask, (a,b),(c,d),(0,255,0), 2)
                        cv2.circle(frame,(a,b),5,color,-1)
                        cv2.putText(frame, str(i), (a,b), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255))
        except IndexError:
            print("Index error")
            End()
            break
        except:
            e = sys.exc_info()[0]
            print(f'TrackWand Error: {e}')
            End()
            break
        img = cv2.add(frame,mask)

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

# def TrackWand():
#     global rval,old_frame,old_gray,p0,mask,color,ig,img,frame

#     try:
#         color = (0,0,255)
#         rval, old_frame = cam.read()
#         cv2.flip(old_frame,1,old_frame)
#         old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
#         equalizeHist(old_gray)
#         old_gray = GaussianBlur(old_gray,(9,9),1.5)
#         dilate_kernel = np.ones(dilation_params, np.uint8)
#         old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)
#         clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
#         old_gray = clahe.apply(old_gray)

#         # Take first frame and find circles in it
#         p0 = cv2.HoughCircles(old_gray,
#                               cv2.HOUGH_GRADIENT,
#                               3,
#                               50,
#                               param1=240,
#                               param2=8,
#                               minRadius=4,
#                               maxRadius=15)
#         if p0 is not None:
#             p0.shape = (p0.shape[1], 1, p0.shape[2])
#             p0 = p0[:,:,0:2]
#             mask = np.zeros_like(old_frame)
#     except Exception as e:
#         print(f'No points found - {e}')
#     # Create a mask image for drawing purposes

#     good_new = None

#     while store.get(f'{redis_ns}:potter_lamp').decode('utf-8') == 'on':
#         try:
#             rval, frame = cam.read()
#             if not isinstance(frame, list):
#                 continue
#             frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             cv2.flip(frame,1,frame)
#             if p0 is not None:
#                 frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#                 equalizeHist(frame_gray)
#                 frame_gray = GaussianBlur(frame_gray,(9,9),1.5)
#                 dilate_kernel = np.ones(dilation_params, np.uint8)
#                 frame_gray = cv2.dilate(frame_gray,
#                                         dilate_kernel,
#                                         iterations=1)
#                 frame_clahe = cv2.createCLAHE(clipLimit=3.0,
#                                             tileGridSize=(8,8))
#                 frame_gray = frame_clahe.apply(frame_gray)

#                 # calculate optical flow
#                 p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray,
#                                                     frame_gray,
#                                                     p0,
#                                                     None,
#                                                     **lk_params)

#                 # Select good points
#                 good_new = p1[st==1]
#                 good_old = p0[st==1]

#                 # draw the tracks
#                 for i,(new,old) in enumerate(zip(good_new,good_old)):
#                     a,b = new.ravel()
#                     c,d = old.ravel()
#                     # only try to detect gesture on highly-rated points 
#                     # (below 10)
#                     if (i<15):
#                         IsGesture(a,b,c,d,i)
#                     dist = math.hypot(a - c, b - d)
#                     if (dist<movment_threshold):
#                         cv2.line(mask, (a,b),(c,d),(0,255,0), 2)
#                     cv2.circle(frame,(a,b),5,color,-1)
#                     cv2.putText(frame,
#                                 str(i),
#                                 (a,b),
#                                 cv2.FONT_HERSHEY_SIMPLEX,
#                                 1.0,
#                                 (0,0,255))
#                 img = cv2.add(frame,mask)

#                 cv2.putText(img, "Press ESC to close.", (5, 25),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255))
#             if debug_opencv:
#                 cv2.imshow("Raspberry Potter", frame)

#             # get next frame
#             rval, frame = cam.read()

#             # Now update the previous frame and previous points
#             old_gray = frame_gray.copy()
#             if good_new is not None:
#                 p0 = good_new.reshape(-1,1,2)
#         except IndexError:
#             print("Index error - Tracking")
#         except Exception as e:
#             print(f'Tracking Error: {e}')
#         # This code is for opencv monitoring window
#         if debug_opencv:
#             key = cv2.waitKey(20)
#             if key in [27, ord('Q'), ord('q')]: # exit on ESC
#                 cv2.destroyAllWindows()
#                 cam.release()
#                 store.set(f'{redis_ns}:potter_lamp', 'off')
#                 break
    
#     # Stop watching for spells
#     if debug_opencv:
#         cv2.destroyAllWindows()
#     cam.release()

def End():
    if cam:
	    cam.close()
    if cv2:
	    cv2.destroyAllWindows()

def WatchSpellsOn():
    """Start watching for spells."""
    store.set(f'{redis_ns}:potter_lamp', 'on')
    # Light up for 5s to let the Wizard know you're ready
    lumos(0)
    # start capturing
    Scan()
    print("Find Wand")
    # FindWand()
    FindNewPoints()
    print("Begin Tracking Wand")
    TrackWand()

def WatchSpellsOff():
    """Stop watching for spells."""
    store.set(f'{redis_ns}:potter_lamp', 'off')
