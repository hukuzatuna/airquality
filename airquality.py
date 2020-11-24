#!/usr/bin/python3

# Philip Moyer (phil@moyer.ai)
# September 2020
#
# Copyright(c) 2020 Philip R. Moyer. All rights reserved.

############################################################################
# airquality.py - calculates and displays indoor AQI
#
# Author:      Phil Moyer (phil@moyer.ai)
# Date:        September 2020
#
# Copyright(c) 2020 Philip R. Moyer. All rights reserved.
#
############################################################################



######################
# Import Libraries
######################

# Standard libraries modules

import json
import statistics
import aqi
import time

# Third-party modules

import board
from board import SCL, SDA
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1305

# Package/application modules


######################
# Globals
######################



######################
# Pre-Main Setup
######################

oled_reset = digitalio.DigitalInOut(board.D4)
WIDTH = 128
HEIGHT = 32
BORDER = 8

i2c = busio.I2C(SCL, SDA)
oled = adafruit_ssd1305.SSD1305_I2C(WIDTH, HEIGHT, i2c)
oled.fill(0)
oled.show()

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("arial.ttf", 24)



######################
# Classes and Methods
######################



######################
# Functions
######################

def main():
    while True:
        with open('/home/pi/shared/src/airquality/aqi.json') as f:
          data = json.load(f)

        pm25 = []
        pm10 = []
        for element in data:
            # print(element)
            pm25.append(element['pm25'])
            pm10.append(element['pm10'])

        # print(statistics.mean(pm25))
        # print(statistics.median(pm25))
        # print('')
        # print(statistics.mean(pm10))
        # print(statistics.median(pm10))

        cur_aqi = aqi.to_iaqi(aqi.POLLUTANT_PM25, statistics.mean(pm25), algo=aqi.ALGO_EPA)

        # format and display
        print("AQI:\t%d" % cur_aqi)

        out_text = "%d" % cur_aqi

        oled.fill(0)
        oled.show()
        image = Image.new("1", (oled.width, oled.height))
        draw = ImageDraw.Draw(image)

        # oled.text(out_text, 5, 15, 1)
        # oled.show()

        (font_width, font_height) = font.getsize(out_text)
        draw.text(
                (oled.width // 2 - font_width //2, oled.height //2 - font_height //2),
                out_text,
                font=font,
                fill=255
        )

        oled.image(image)
        oled.show()

        time.sleep(300)



######################
# Main
######################

# The main code call allows this module to be imported as a library or
# called as a standalone program because __name__ will not be properly
# set unless called as a program.

if __name__ == "__main__":
    main()

