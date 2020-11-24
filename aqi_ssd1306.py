#!/usr/bin/python3 

############################################################################
# aqi_sds1306.py - Calculete and display air quality index on the
# attached ssd1306 display.
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

import time
import statistics
import pandas as pd

# Third-party modules

import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_ssd1306		# OLED display
import mysql.connector
import aqi

# Package/application modules

from secrets import secrets


######################
# Globals
######################



######################
# Classes and Methods
######################


######################
# Pre-Main Setup
######################

cur_user = secrets["sqluser"]
cur_pwd = secrets["sqlpasswd"]



######################
# Functions
######################

def main():
    # Create the I2C interface.
    i2c = busio.I2C(board.SCL, board.SDA)

    # 128x32 OLED Display
    reset_pin = DigitalInOut(board.D4)
    display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, reset=reset_pin)

    # Clear the display.
    display.fill(0)
    display.show()
    width = display.width
    height = display.height

    # prepare scrolling display
    dline1 = dline2 = dline3 = ""

    while True:
        aqi_cnx = mysql.connector.connect(user=cur_user, password=cur_pwd,
                                   host='sequoia', database='airquality')
        aqi_cursor = aqi_cnx.cursor()

        # Fetch data from mySQL database
        data_fetch = "SELECT * FROM pm25data WHERE ts >= date_sub(now(),interval 1 hour)"
        aqi_cursor.execute(data_fetch)
        ds1_records = aqi_cursor.fetchall()
        ds1DF = pd.DataFrame(ds1_records)
        try:
            ds1DF.columns = [
                        'observation',
                        'ts',
                        'pm25',
                        'pm100',
                        'mtempc',
                        'mtempf',
                        'mpress',
                        'mrh'
            ]
        except ValueError as e:
            print("Caught ValueError: %s" % e)
            time.sleep(10)
            continue

        meanpm25 = statistics.mean(ds1DF['pm25'])
        meanpm100 = statistics.mean(ds1DF['pm100'])
        cur_aqi = aqi.to_aqi([
            (aqi.POLLUTANT_PM25, meanpm25),
            (aqi.POLLUTANT_PM10, meanpm100)
        ])

        data_fetch = "SELECT * FROM pm25data ORDER BY observation DESC LIMIT 1"
        aqi_cursor.execute(data_fetch)
        ds2_records = aqi_cursor.fetchall()
        ds2DF = pd.DataFrame(ds2_records)
        try:
            ds2DF.columns = [
                        'observation',
                        'ts',
                        'pm25',
                        'pm100',
                        'mtempc',
                        'mtempf',
                        'mpress',
                        'mrh'
            ]
        except ValueError as e:
            print("Caught ValueError: %s" % e)
            time.sleep(10)
            continue

        aqi_cursor.close()
        aqi_cnx.close()

        cur_tempc = ds2DF['mtempc']
        cur_tempf = ds2DF['mtempf']
        cur_press = ds2DF['mpress']
        cur_rh = ds2DF['mrh']

        dline1 = "%0.2f C  %0.2f F" % (cur_tempc, cur_tempf)
        dline2 = "%0.2f hPa  %0.2f RH" % (cur_press, cur_rh)
        dline3 = "AQI %d" % cur_aqi

        print(dline1)
        print(dline2)
        print("%s\n" % dline3)

        display.fill(0)
        display.text(dline1, 5, 0, 1)
        display.text(dline2, 5, 11, 1)
        display.text(dline3, 5, 22, 1)
        display.show()

        time.sleep(120)



######################
# Main
######################

# The main code call allows this module to be imported as a library or
# called as a standalone program because __name__ will not be properly
# set unless called as a program.

if __name__ == "__main__":
    main()


