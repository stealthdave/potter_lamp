'''
Control the IR emitters.
'''

import RPi.GPIO as GPIO
from config import potter_lamp_config as config

# IR LED emitters control
emitters_pin = config['emitters_pin']
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(emitters_pin, GPIO.OUT)

def set_emitters(state=False):
    gpio_state = GPIO.HIGH if state else GPIO.LOW
    GPIO.output(emitters_pin, gpio_state)
    return state
