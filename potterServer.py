#!/bin/python
"""
This server handles the casting of "spells" that are identified by a separate,
more powerful server used to identify said spells.  It also handles turning
on and off the IR emitters which can get hot if they're left on all the time.
"""

from flask import Flask
import RPi.GPIO as GPIO
import threading

from spells import lumos, nox, incendio, colovaria
from config import potter_lamp_config as config
from wand import WatchSpellsOn, WatchSpellsOff

app = Flask(__name__)

# IR LED emitters control
emitters_pin = 17
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(emitters_pin, GPIO.OUT)
GPIO.output(emitters_pin, GPIO.LOW) # default OFF


@app.route('/')
def index():
    """Video streaming home page."""
    return "Select a spell to cast."

@app.route('/spells/lumos')
def cast_lumos():
    spell = threading.Thread(target=lumos)
    spell.start()
    return "lumos on"

@app.route('/spells/incendio')
def cast_incendio():
    spell = threading.Thread(target=incendio)
    spell.start()
    return "incendio on"

@app.route('/spells/colovaria')
def cast_colovaria():
    spell = threading.Thread(target=colovaria)
    spell.start()
    return "colovaria on"

@app.route('/spells/nox')
def cast_nox():
    spell = threading.Thread(target=nox)
    spell.start()
    return "nox on"

@app.route('/emitters/on')
def emitters_on():
    # Turn on IR LED emitters.
    GPIO.output(emitters_pin, GPIO.HIGH)

@app.route('/emitters/off')
def emitters_off():
    # Turn off IR LED emitters.
    GPIO.output(emitters_pin, GPIO.LOW)

@app.route('/wand/on')
def wand_on():
    """Start watching for spells."""
    # Turn on IR LED emitters for wand detection.
    GPIO.output(emitters_pin, GPIO.HIGH)
    wand = threading.Thread(target=WatchSpellsOn)
    wand.start()
    return "wand on"

@app.route('/wand/off')
def wand_off():
    """Stop watching for spells."""
    # Turn off IR LED emitters for wand detection.
    GPIO.output(emitters_pin, GPIO.LOW)
    WatchSpellsOff()
    return "wand off"


if config['watch_on_start']:
    print("Watch for spells autostarted.")
    wand_on()

if __name__ == '__main__':
    app.run(host=config['host'], port=config['port'], debug=True, threaded=True)

