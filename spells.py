#!/bin/python
"""
This server handles the casting of "spells" that are identified by a separate,
more powerful server used to identify said spells.  It also handles turning
on and off the IR emitters which can get hot if they're left on all the time.
"""

import board
import neopixel
import time
import random
import redis
import json


# LED light strip setup
pixels = neopixel.NeoPixel(board.D18, 60)
pixels.fill((0,0,0))

# Use redis to track state of lights
store = redis.Redis() # defaults for localhost will work just fine
store.set('potter_lights', 'off')

def set_current_color(color):
    """Set the current color of the lamp. (Used by Nox.)"""
    store.set('potter_current_color', json.dumps(color))

def get_current_color():
    """Get current color of the lamp."""
    color = json.loads(store.get('potter_current_color').decode('utf-8'))
    return tuple(color)

def get_lights_state():
    """Returns True is lights are on; False if off or turning off."""
    return store.get('potter_lights').decode('utf-8') == 'on'

def set_lights_state(light_status):
    """Sets the state of 'potter_lights' to 'on' or 'off'."""
    status_text = 'on' if light_status else 'off'
    store.set('potter_lights', status_text)
    print(status_text)
    return status_text


# set initial color
set_current_color((0,0,0))

# SPELLS

def lumos():
    """Lumos - light up the lantern."""
    duration = 3
    set_lights_state(True)
    for val in range(256):
        # if someone casts "Nox", stop turning on lights
        if not get_lights_state():
            break
        color = (val, val, val)
        set_current_color(color)
        pixels.fill(color)
        time.sleep(duration / 256)
    # If the lights are still on, run nox.
    if get_lights_state():
        nox()
    return "lumos complete"

def nox():
    """Nox - turn off the light."""
    set_lights_state(False)
    color = get_current_color()
    for val in range(64):
        pr = int((255 - val * 4) / 256 * color[0])
        pg = int((255 - val * 4) / 256 * color[1])
        pb = int((255 - val * 4) / 256 * color[2])
        pixels.fill((pr, pg, pb))
        time.sleep(0.001)
    # complete fade to black
    pixels.fill((0, 0, 0))
    set_current_color((0, 0, 0))
    return "nox complete"

def incendio():
    """Incendio - FIRE!!!"""
    duration = 300 # burn for 5 minutes
    interval = 0.1 # change the flame every 1/10s
    set_lights_state(True)
    while duration > 0 and get_lights_state():
        current_color = get_current_color()
        color = (random.randint(100, 255), random.randint(0, 40), 0)
        for val in range(10):
            pixels.fill((
                int(current_color[0] + ((color[0] - current_color[0]) * val / 10)),
                int(current_color[1] + ((color[1] - current_color[1]) * val / 10)),
                int(current_color[2] + ((color[2] - current_color[2]) * val / 10)),
            ))
            time.sleep(0.0125)
        set_current_color(color)
        pixels.fill(color)
        time.sleep(interval)
        duration = duration - interval
    nox()
    return "incendio complete"
