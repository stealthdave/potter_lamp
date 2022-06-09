# Harry Potter Lamp
Cast "spells" at a modified oil lamp powered by a Raspberry Pi 3 with NOIR 
camera and LED light strip for effects.

# THIS IS A WORK IN PROGRESS!!!
Parts of the system work, but the wand tracking system does not... yet.
Spells can be "cast" and lighting effects triggered via API calls.  Wand
tracking can be turned on and off via API calls, as can the IR emitters.

Hardware used:
* Oil lamp (modified) https://www.amazon.com/gp/product/B000BQSFP0/
* Raspberry Pi 3B https://www.amazon.com/gp/product/B01CD5VC92/
* NeoPixel LED Light Strip (for lighting effects)
* NOIR 8MP Camera with IR pass filter https://www.amazon.com/gp/product/B01ER2SMHY/
* Super Bright IR LEDs https://www.amazon.com/gp/product/B00ULB0U44/
* 2N2222 Transistor and resistors to control IR LEDs with GPIO
* Wand from Ollivanders' Wand Shop (or other wand with IR reflective tip)

My original intent was to use `APA102` LED lights as they had a lot of support
for Raspberry Pi controls, particularly with Python, my current server-side
language of choice.  However, the vendor that I purchased them from on eBay
sent me a NeoPixel compatible set of LED lights instead.  This works, but at
the expense of having to run the script as root due to the timing controls
necessary for the NeoPixel.  Keep this in mind when choosing your login
credentials for your Raspberry Pi.

# Software Installation

The software setup assumes that you are running Raspberry Pi OS Debian Minimal
(no desktop).  This implementation of the Harry Potter lamp requires the
following software:

* Debian GNU/Linux 11 (Bullseye) Minimal (no desktop) for Raspberry Pi
* Python 3 with Virtual Environments
* OpenCV 4.5.x with Python bindings
* redis (primarily for communcation between threads)

## Install Requirements

Run the following commands to install:

```
sudo apt update && sudo apt -y upgrade
sudo apt install python3-venv python3-opencv python3-pip redis
sudo apt-get install libhdf5-dev libhdf5-serial-dev libhdf5-103
sudo apt-get install libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
sudo apt-get install libatlas-base-dev
sudo apt-get install libjasper-dev
```

## Create Virtual Environment

Create the virtual environment for your lamp.

```
python3 -m venv lampvenv
source ./lampvenv/bin/activate
python3 -m pip install -r requirements.txt
```

## Run the server
Copy the example config file.  The server should run with the example 
unmodified, but you can change the port number, redis namespace and other
settings here if desired.

```
cp config.example.py config.py
```

Due to the requirements of the NeoPixels driver, the server _must_ be run as 
root!

```
sudo ./lampvenv/bin/python3 potterServer.py
```

## Call REST endpoints to watch for spells
By default, the Potter Lamp script is _not_ watching for spells, and a REST 
endpoint must be called in order to start.  The idea behind this is to have an
easy way to start and stop the server.  The IR emitters alone use a lot of
power and generate a fair amount of heat, making it unsafe to have them on all
the time.  In my own use case, I use IFTTT to use an Alexa voice command to
start the server. e.g., "Alexa, Let's cast some spells!"  Here are the
currently available endpoints:

* `/wand/on` - Start watching for spells.
* `/wand/off` - Stop watching for spells.
* `/wand/watch` - View the OpenCV processed image (debug mode must be on)
* `/emitters/on` - Turn on IR emitters independently of watching for spells.
* `/emitters/off` - Turn off IR emitters.
* `/spells/*` - Cast a "spell" manually, e.g. "lumos" or "nox"


# Acknowledgements
Inspired by many other Harry Potter Spell projects including:

* Adam Thole Smart Home Control Wand - https://www.adamthole.com/control-smart-home-with-magic-wand-video/
* Raspberry Potter - https://www.raspberrypotter.net/ | https://github.com/sean-obrien/rpotter

Other related tutorials and libraries:
* https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage
* https://circuitpython.readthedocs.io/projects/neopixel/en/latest/api.html
* https://www.pyimagesearch.com/2018/09/19/pip-install-opencv/
