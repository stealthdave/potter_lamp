#!/bin/python
"""
This server handles the casting of "spells" that are identified by a separate,
more powerful server used to identify said spells.  It also handles turning
on and off the IR emitters which can get hot if they're left on all the time.
"""

from flask import Flask
import RPi.GPIO as GPIO

from spells import lumos, nox, incendio

app = Flask(__name__)

# IR LED emitters control
emitters_pin = 17
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(emitters_pin, GPIO.OUT)


@app.route('/')
def index():
    """Video streaming home page."""
    return "Select a spell to cast."

@app.route('/spells/lumos')
def cast_lumos():
    return lumos()

@app.route('/spells/nox')
def cast_nox():
    return nox()

@app.route('/spells/incendio')
def cast_incendio():
    return incendio()

@app.route('/emitters/on')
def emitters_on():
    """Turn on IR LED emitters for wand detection."""
    GPIO.output(emitters_pin, GPIO.HIGH)
    return "emitters on"

@app.route('/emitters/off')
def emitters_off():
    """Turn off IR LED emitters for wand detection."""
    GPIO.output(emitters_pin, GPIO.LOW)
    return "emitters off"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

