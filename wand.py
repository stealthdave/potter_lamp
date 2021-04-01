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

import numpy as np
import cv2
import picamera
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

# Use redis to track state of lamp
redis_ns = config["redis_namespace"]
store = redis.Redis() # defaults for localhost will work just fine

def LampState(set=None):
    """Retrieve or set lamp state."""
    if set in ['on', 'off']:
        store.set(f'{redis_ns}:potter_lamp', set)
        lamp_state = set == 'on'
        set_emitters(lamp_state)
        print(f'Set Lamp State: {lamp_state}')
    else:
        lamp_state = store.get(f'{redis_ns}:potter_lamp').decode('utf-8') == 'on'

    return lamp_state

# Set default lamp state
LampState('off')

# OpenCV Parameters for image processing
lk_params = dict( winSize  = (15,15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
dilation_params = (5, 5)
movment_threshold = 80

# Spells
spells_list = {
    "!right!up": "lumos",
    "!right!down": "nox",
    "!left!up": "incendio",
    "!left!down": "colovaria"
}

def StartCamera():
    """Initialize camera input."""
    # Open a window for debug
    if debug_opencv:
        cv2.namedWindow("Raspberry Potter")
    # Initialize camera
    try:
        cam = cv2.VideoCapture(0)
        cam.set(3, 640)
        cam.set(4, 480)
        print('Camera started')
        return cam
    except Exception as camera:
        print('Camera already open')


def IsGesture(a,b,c,d,i,ig):
    """
    Determines if the point has moved.
    """

    spell_cast = False
    #look for basic movements - TODO: trained gestures
    if ((a<(c-5))&(abs(b-d)<2)):
        ig[i].append("!left")
    elif ((c<(a-5))&(abs(b-d)<2)):
        ig[i].append("!right")
    elif ((b<(d-5))&(abs(a-c)<5)):
        ig[i].append("!up")
    elif ((d<(b-5))&(abs(a-c)<5)):
        ig[i].append("!down")
    #these are for moving diagnally
	#Angle Down Left = ADL
    elif (((b-d)/(c-a))>0.9):
	    ig[i].append("!ADL")
	#Angle Down Right = ADR
    elif (((b-d)/(a-c))>0.9):
	    ig[i].append("!ADR")
	#Angle Up Right = AUR
    elif (((d-b)/(a-c))>0.9):
	    ig[i].append("!AUR")
    # PART 5B 
    #check for gesture patterns in array
    astr = ''.join(map(str, ig[i]))

    # Look for spells in the casting string
    for motion, spell in spells_list.items():
        if motion in astr:
            cast_spell(spell)
            print(f'Spell "{spell}" cast for point {i} string: {astr}')
            spell_cast = True

    return ig, spell_cast


def FindWand(cam,
             rval=None,
             old_frame=None,
             old_gray=None,
             p0=None,
             mask=None,
             color=None,
             ig=None):
    """
    FindWand is called to find all potential wands in a scene.  These are then 
    tracked as points for movement.  The scene is reset every 3 seconds.
    """

    try:
        rval, old_frame = cam.read()
        cv2.flip(old_frame,1,old_frame)
        old_gray = cv2.cvtColor(old_frame,cv2.COLOR_BGR2GRAY)
        cv2.equalizeHist(old_gray)
        old_gray = cv2.GaussianBlur(old_gray,(9,9),1.5)
        dilate_kernel = np.ones(dilation_params, np.uint8)
        old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        old_gray = clahe.apply(old_gray)
        #TODO: trained image recognition
        p0 = cv2.HoughCircles(old_gray,cv2.HOUGH_GRADIENT,3,50,param1=240,param2=8,minRadius=4,maxRadius=15)
        if p0 is not None:
            p0.shape = (p0.shape[1], 1, p0.shape[2])
            p0 = p0[:,:,0:2]
            mask = np.zeros_like(old_frame)
            ig = [[0] for x in range(20)]

    except Exception as e:
        print(f'Error: {e}')
        End(cam)
        exit
    
    print("finding...")
    return rval,old_frame,old_gray,p0,mask,color,ig


def TrackWand():
    """
    Tracks wand points for 3 seconds.
    """
    wand_timeout = config["wand_timeout"]
    cam = StartCamera()
    if not cam:
        print('=== NO CAMERA FOUND ===')
        WatchSpellsOff()
        exit

    wand_timer = time.time() + wand_timeout
    rval,old_frame,old_gray,p0,mask,color,ig = FindWand(cam)
    # Loop every 3 seconds until a wand is found
    while rval is None and time.time() < wand_timer:
        time.sleep(3)
        rval,old_frame,old_gray,p0,mask,color,ig = FindWand(cam)

    # check if we've started the scene successfully within timeout
    if rval is None:
        print('Scene not started.')
        WatchSpellsOff()
        exit

    try:
        color = (0,0,255)
        rval, old_frame = cam.read()
        cv2.flip(old_frame,1,old_frame)
        old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
        cv2.equalizeHist(old_gray)
        old_gray = GaussianBlur(old_gray,(9,9),1.5)
        dilate_kernel = np.ones(dilation_params, np.uint8)
        old_gray = cv2.dilate(old_gray, dilate_kernel, iterations=1)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        old_gray = clahe.apply(old_gray)

        # Take first frame and find circles in it
        p0 = cv2.HoughCircles(old_gray,cv2.HOUGH_GRADIENT,3,50,param1=240,param2=8,minRadius=4,maxRadius=15)
        if p0 is not None:
            p0.shape = (p0.shape[1], 1, p0.shape[2])
            p0 = p0[:,:,0:2]
            mask = np.zeros_like(old_frame)
    except Exception as e:
        print("No points found")
    # Create a mask image for drawing purposes
    find_wand_timer = time.time() + 3
    wand_timer = time.time() + wand_timeout
    while LampState() and time.time() < wand_timer:
        try:
            rval, frame = cam.read()
            cv2.flip(frame,1,frame)
            if p0 is not None:
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cv2.equalizeHist(frame_gray)
                frame_gray = cv2.GaussianBlur(frame_gray,(9,9),1.5)
                dilate_kernel = np.ones(dilation_params, np.uint8)
                frame_gray = cv2.dilate(frame_gray, dilate_kernel, iterations=1)
                frame_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                frame_gray = frame_clahe.apply(frame_gray)

                # calculate optical flow
                p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

                # Select good points
                good_new = p1[st==1]
                good_old = p0[st==1]

                # draw the tracks
                for i,(new,old) in enumerate(zip(good_new,good_old)):
                    a,b = new.ravel()
                    c,d = old.ravel()
                    # only try to detect gesture on highly-rated points (below 10)
                    if (i<15):
                        ig, spell_cast = IsGesture(a,b,c,d,i,ig)
                        # reset timer if spell is cast
                        if spell_cast:
                            wand_timer = time.time() + wand_timeout
                    dist = math.hypot(a - c, b - d)
                    if (dist<movment_threshold):
                        cv2.line(mask, (a,b),(c,d),(0,255,0), 2)
                    cv2.circle(frame,(a,b),5,color,-1)
                    cv2.putText(frame, str(i), (a,b), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255)) 
                img = cv2.add(frame,mask)
                # save for debug
                cv2.imwrite('test.jpg', img)

            if debug_opencv:
                cv2.imshow("Raspberry Potter", frame)

            # get next frame
            rval, frame = cam.read()

            # Now update the previous frame and previous points
            old_gray = frame_gray.copy()
            p0 = good_new.reshape(-1,1,2)
        except IndexError:
            print("Index error - Tracking")  
        except Exception as error:
            e = sys.exc_info()[0]
            print("Tracking Error: %s" % e)
        
        # Scene resets every 3 seconds
        if time.time() > find_wand_timer:
            rval,old_frame,old_gray,p0,mask,color,ig = FindWand(cam,rval,old_frame,old_gray,p0,mask,color,ig)
            find_wand_timer = time.time() + 3
    
    # The End
    End(cam)
    WatchSpellsOff()

def End(cam):
    # Stop IR emitter
    LampState('off')
    print('=== END ===')
    try:
	    cam.close()
    except Exception as e:
        print('Camera not found.')
    cv2.destroyAllWindows()

def WatchSpellsOn():
    """Start watching for spells."""
    LampState('on')
    # Light up for 5s to let the Wizard know you're ready
    lumos(0)
    # track wand
    print("Begin Tracking Wand")
    TrackWand()

def WatchSpellsOff():
    """Stop watching for spells."""
    LampState('off')
    # Light up for 5s to let the Wizard know you're done
    lumos(0, (127, 10, 10))
