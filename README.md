# Harry Potter Lamp
Cast "spells" at a modified oil lamp powered by a Raspberry Pi 3 with NOIR camera and LED light strip for effects.

Hardware used:
* Oil lamp (modified) https://www.amazon.com/gp/product/B000BQSFP0/
* Raspberry Pi 3B https://www.amazon.com/gp/product/B01CD5VC92/
* NeoPixel LED Light Strip (for lighting effects)
* NOIR 8MP Camera with IR pass filter https://www.amazon.com/gp/product/B01ER2SMHY/
* IR LED lights https://www.amazon.com/gp/product/B07FM6LL3V/
* 3.3V relay (to toggle IR LED lights) https://www.amazon.com/gp/product/B07XGZSYJV/
* Wand from Ollivanders' Wand Shop (or other wand with IR reflective tip)

My original intent was to use `APA102` LED lights as they had a lot of support for Raspberry Pi controls, particularly with Python, my current server-side language of choice.  However, the vendor that I purchased them from on eBay sent me a NeoPixel compatible set of LED lights instead.  This works, but at the expense of having to run the script as root due to the timing controls necessary for the NeoPixel.  Keep this in mind when choosing your login credentials for your Raspberry Pi.

# Software Installation

The software setup assumes that you are running Raspberry Pi OS Debian Minimal (no desktop).  This implementation of the Harry Potter lamp requires the following software:

* Python 3 with Virtual Environments
* OpenCV 3.2.0 with Python bindings
* redis

## Install Requirements

Run the following commands to install:

```
sudo apt update && sudo apt -y upgrade
sudo apt install python3-venv python3-opencv python3-pip redis
```

## Create Virtual Environment

Create the virtual environment for your lamp.

```
python3 -m venv lampvenv
python3 -m pip install -r requirements.txt
```

## Run the server
Due to the requirements of the NeoPixels driver, the server _must_ be run as root!

```
sudo ./lampvenv/bin/python3 potterServer.py
```

# Acknowledgements
Inspired by many other Harry Potter Spell projects including:

Adam Thole Smart Home Control Wand - https://www.adamthole.com/control-smart-home-with-magic-wand-video/
Raspberry Potter - https://www.raspberrypotter.net/

Other related tutorials and libraries:
* https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage
* https://circuitpython.readthedocs.io/projects/neopixel/en/latest/api.html

