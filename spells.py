"""
This server handles the casting of "spells" that are identified by a separate
server used to identify said spells.  It also handles turning on and off the IR
emitters which can get hot if they're left on all the time.
"""

import board
import neopixel
import time
import random
import redis
import threading
import pickle
from config import potter_lamp_config as config

# LED light strip setup
pixels = neopixel.NeoPixel(board.D18, 60)
pixels.fill((0,0,0))

# Use redis to track state of lights
redis_ns = config["redis_namespace"]
store = redis.Redis() # defaults for localhost will work just fine

def store_set(key, value):
    store.set(f'{redis_ns}:{key}', pickle.dumps(value))

def store_get(key):
    return pickle.loads(store.get(f'{redis_ns}:{key}'))

store_set('potter_lights', 'off')
store_set('current_spell', '')

def set_current_color(color):
    """Set the current color of the lamp. (Used by Nox.)"""
    store_set('potter_current_color', color)

def get_current_color():
    """Get current color of the lamp."""
    return store_get('potter_current_color')

def get_lights_state():
    """Returns True is lights are on; False if off or turning off."""
    return store_get('potter_lights') == 'on'

def set_lights_state(light_status):
    """Sets the state of 'potter_lights' to 'on' or 'off'."""
    status_text = 'on' if light_status else 'off'
    store_set('potter_lights', status_text)
    print(f'lights status: {status_text}')
    return status_text

def check_current_spell(spell):
    """Checks if 'spell' is the currently cast spell."""
    return store_get('current_spell') == spell


# set initial color
set_current_color((0,0,0))

# SPELLS

def lumos(lamp_duration=180, start_color=(255, 255, 255), direct_cast = False):
    """Lumos - light up the lantern."""
    print('start lumos')
    duration = 3
    set_lights_state(True)
    for val in range(0, 255, 4):
        # if someone casts "Nox", stop turning on lights
        if not get_lights_state() or not check_current_spell('lumos'):
            break
        color = (int(val * start_color[0] / 256),
                 int(val * start_color[1] / 256),
                 int(val * start_color[2] / 256))
        set_current_color(color)
        pixels.fill(color)
        time.sleep(duration / 256)

    # Keep the lights on (default 3 minutes)
    time.sleep(lamp_duration)

    # If the lights are still on, run nox.
    if get_lights_state() and check_current_spell('lumos'):
        nox()
    print("lumos complete")
    return

def nox():
    """Nox - turn off the light."""
    set_lights_state(False)
    color = get_current_color()
    for val in range(0, 255, 4):
        pr = int((255 - val) / 256 * color[0])
        pg = int((255 - val) / 256 * color[1])
        pb = int((255 - val) / 256 * color[2])
        pixels.fill((pr, pg, pb))
        time.sleep(0.001)
    # complete fade to black
    pixels.fill((0, 0, 0))
    set_current_color((0, 0, 0))
    print("nox complete")
    # All spells end in Nox
    store_set('current_spell', '')
    return

def incendio(lamp_duration=180):
    """Incendio - FIRE!!!"""
    duration = lamp_duration # burn for 3 minutes by default
    interval = 0.1 # change the flame every 1/10s
    set_lights_state(True)
    while duration > 0 and get_lights_state() and check_current_spell('incendio'):
        current_color = get_current_color()
        color = (random.randint(100, 255), random.randint(0, 40), 0)
        for val in range(10):
            pixels.fill((
                int(current_color[0] + ((color[0] - current_color[0]) * val / 10)),
                int(current_color[1] + ((color[1] - current_color[1]) * val / 10)),
                int(current_color[2] + ((color[2] - current_color[2]) * val / 10)),
            ))
            time.sleep(0.003)
        set_current_color(color)
        pixels.fill(color)
        time.sleep(interval)
        duration = duration - interval
    if check_current_spell('incendio'):
        nox()
    print("incendio complete")
    return

def colovaria(lamp_duration=180):
    """Colovaria - lots of colors"""
    duration = lamp_duration # kaleidascope for 3 minutes by default
    interval = 0.2 # change the color every 2/10s
    set_lights_state(True)
    while duration > 0 and get_lights_state() and check_current_spell('colovaria'):
        current_color = get_current_color()
        color = (
            random.randint(20, 255),
            random.randint(20, 255),
            random.randint(20, 255)
        )
        #TODO: Make multiple colors
        for val in range(10):
            pixels.fill((
                int(current_color[0] + ((color[0] - current_color[0]) * val / 10)),
                int(current_color[1] + ((color[1] - current_color[1]) * val / 10)),
                int(current_color[2] + ((color[2] - current_color[2]) * val / 10)),
            ))
            time.sleep(0.003)
        set_current_color(color)
        pixels.fill(color)
        time.sleep(interval)
        duration = duration - interval
    if check_current_spell('colovaria'):
        nox()
    print("colovaria complete")
    return

def cast_spell(spell):
    cast = None
    if spell == 'lumos':
        cast = threading.Thread(target=lumos)
    elif spell == 'nox':
        cast = threading.Thread(target=nox)
    elif spell == 'incendio':
        cast = threading.Thread(target=incendio)
    elif spell == 'colovaria':
        cast = threading.Thread(target=colovaria)

    if cast is not None:
        store_set('current_spell', spell)
        cast.start()
    
    return cast