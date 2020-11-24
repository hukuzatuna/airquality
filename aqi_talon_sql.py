#!/usr/bin/python3
############################################################################
# aqi_talon_sql.py - collect data from attached SGP30 and Adafruit
# I2C PM2.5 sensor.
#
# Author:      Phil Moyer (phil@moyer.ai)
# Date:        November 2020
#
# Copyright(c) 2020 Philip R. Moyer. All rights reserved.
#
############################################################################


######################
# Import Libraries
######################

# Standard libraries modules

import time
import mysql.connector
import statistics

# Third-party modules

import board
from board import SCL, SDA
import busio
import digitalio
import adafruit_bme680
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C
import adafruit_sgp30
import aqi

# Package/application modules

from secrets import secrets


######################
# Globals
######################

reset_pin = None
temp_offset = -2.5


######################
# Classes and Methods
######################



######################
# Pre-Main Setup
######################

oled_reset = digitalio.DigitalInOut(board.D4)

WIDTH = 128
HEIGHT = 64
BORDER = 8

# i2c = busio.I2C(SCL, SDA)
i2c = busio.I2C(SCL, SDA, frequency=100000)
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

cur_user = secrets["sqluser"]
cur_pwd = secrets["sqlpasswd"]

# Connect to a PM2.5 sensor over I2C
pm25 = PM25_I2C(i2c, reset_pin)



######################
# Functions
######################

def c_to_f(tempc):
    return((tempc * 1.8000000) + 32.00)


def main():
    # SGP30 startup
    # print("SGP30 serial #", [hex(i) for i in sgp30.serial])
    sgp30.iaq_init()
    sgp30.set_iaq_baseline(0x8973, 0x8AAE)
    elapsed_sec = 0

    aqi_cnx = mysql.connector.connect(user=cur_user, password=cur_pwd,
                               host='sequoia', database='airquality')
    aqi_cursor = aqi_cnx.cursor()

    # Get SGP30 calibration baseline - use it if it's in the database
    base_query = "SELECT observation,baseeco2,basetvoc FROM outbase ORDER BY observation DESC LIMIT 1"
    aqi_cursor.execute(base_query)
    base_data = aqi_cursor.fetchall()
    if len(base_data) > 1:
        hist_eco2_base = base_data[1]
        hist_tvoc_base = base_data[2]
        sgp30.set_iaq_baseline(hist_eco2_base, hist_tvoc_base)
    else:
        hist_eco2_base = None
        hist_tvoc_base = None
    aqi_cursor.close()
    aqi_cnx.close()


    while True:

        aqi_cnx = mysql.connector.connect(user=cur_user, password=cur_pwd,
                                   host='sequoia', database='airquality')
        aqi_cursor = aqi_cnx.cursor()

        cur_eco2 = 400
        cur_tvoc = 0
        i_cnt = 0
        while 400 == cur_eco2 or 0 == cur_tvoc:
            i_cnt += 1
        # for icnt in range(1,21):
            # print("Calibrating eCO2 = %d ppm \t TVOC = %d ppb" % (sgp30.eCO2, sgp30.TVOC))
            cur_eco2 = sgp30.eCO2
            cur_tvoc = sgp30.TVOC
            time.sleep(1)
            elapsed_sec += 1
            if elapsed_sec > 20:
                elapsed_sec = 0
                # print(
                   #  "**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x"
                   #  % (sgp30.baseline_eCO2, sgp30.baseline_TVOC)
                # )
                # Insert data into mySQL database

                data_insert = (
                    "INSERT INTO outbase(baseeco2,basetvoc) "
                    " VALUES (%s,%s) "
                )
                insert_data = (
                        sgp30.baseline_eCO2,
                        sgp30.baseline_TVOC
                )
                aqi_cursor.execute(data_insert, insert_data)
                aqi_cnx.commit()
            if 90 < i_cnt:
                print("SGP30 calibration failed, continuing")
                break

        time.sleep(1)
        try:
            aqdata = pm25.read()
            # print(aqdata)
        except RuntimeError:
            print("Unable to read from sensor, retrying...")
            continue

        # Concentration Units (standard)
        print("PM 1.0: %d\tPM2.5: %d\tPM10: %d"
            % (aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"])
        )
        # print("%02f C, %0.2f F, RH %0.2f, %0.2f hPa" % ((bme680.temperature + temp_offset),
        #   c_to_f((bme680.temperature+temp_offset)),
        #   bme680.humidity,
        #   bme680.pressure))

        cur_aqi = aqi.to_aqi([
            (aqi.POLLUTANT_PM25, aqdata["pm25 standard"]),
            (aqi.POLLUTANT_PM10, aqdata["pm100 standard"])
            ])

        print("eCO2: %0.2f PPM, TVOC: %0.2f PPB" % (cur_eco2, cur_tvoc))
        print("AQI: %2d" % cur_aqi)

        # Insert data into mySQL database

        data_insert = (
            "INSERT INTO aqdata2(pm25,pm100,aqi,eco2,tvoc) "
            " VALUES (%s,%s,%s,%s,%s) "
        )

        insert_data = (
                aqdata["pm25 standard"],
                aqdata["pm100 standard"],
                cur_aqi,
                cur_eco2,
                cur_tvoc
        )

        aqi_cursor.execute(data_insert, insert_data)
        aqi_cnx.commit()

        aqi_cursor.close()
        aqi_cnx.close()

        # Print data line

        time.sleep(150)


######################
# Main
######################

# The main code call allows this module to be imported as a library or
# called as a standalone program because __name__ will not be properly
# set unless called as a program.

if __name__ == "__main__":
    main()

