#!/bin/python
"""
This server handles the casting of "spells" that are identified by a separate,
more powerful server used to identify said spells.  It also handles turning
on and off the IR emitters which can get hot if they're left on all the time.
"""

from flask import Flask
import threading

from spells import lumos, nox, incendio, colovaria
from config import potter_lamp_config as config
from wand import WatchSpellsOn, WatchSpellsOff, WatchSpellsStatus
from emitters import set_emitters

app = Flask(__name__)


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
    set_emitters(True)
    return "ir emitters on"

@app.route('/emitters/off')
def emitters_off():
    # Turn off IR LED emitters.
    set_emitters(False)
    return "ir emitters off"

@app.route('/wand/on')
def wand_on():
    """Start watching for spells."""
    wand = threading.Thread(target=WatchSpellsOn)
    wand.start()
    return "wand on"

@app.route('/wand/off')
def wand_off():
    """Stop watching for spells."""
    WatchSpellsOff()
    return "wand off"

@app.route('/wand/status')
def wand_status():
    """Check status of watching for spells."""
    return "wand on" if WatchSpellsStatus() else "wand off"


if config['watch_on_start']:
    print("Watch for spells autostarted.")
    wand_on()

if __name__ == '__main__':
    app.run(host=config['host'], port=config['port'], debug=False, threaded=True)

