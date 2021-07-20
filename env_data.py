# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

 

import numpy as np
import time
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C
import adafruit_scd30
import adafruit_bme680

reset_pin = None


# Create library object, use 'slow' 100KHz frequency!
i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
# Connect to a PM2.5 sensor over I2C
pm25 = PM25_I2C(i2c, reset_pin)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
bme_temperature_offset = -1.5

scd = adafruit_scd30.SCD30(i2c)
scd.measurement_interval = 2

scd.temperature_offset = 7
scd.self_calibration_enabled = True
#scd.forced_recalibration_reference = 416

# print("Found PM2.5 sensor, reading data...")

def env_av(total,sec):
	readings = int(total / sec)
	values = np.empty([readings - 0, 19], dtype = "float32")

	for i in range(0,readings - 0):
		start = time.time()
		aqdata = pm25.read()

	
		values[i] = [aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"], aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"], aqdata["particles 03um"], aqdata["particles 05um"], aqdata["particles 10um"], aqdata["particles 25um"], aqdata["particles 50um"], aqdata["particles 100um"], scd.CO2, scd.temperature, scd.relative_humidity, bme680.temperature + bme_temperature_offset, bme680.gas, bme680.relative_humidity, bme680.pressure]
		realsec = sec + start - time.time()
		time.sleep(realsec)
	return np.average(values, axis = 0)


aqi25 = [0,12,35.5,55.5,150.5,250.5,500.5,10000]
aqi10 = [0,55,155,255,355,425,605,10000]
breakpoints = [0, 50, 100, 150, 200, 300, 500, 10000]

def piecewise_convert(conc,values):
	aqi=0
	for i in range(0,len(values)):
		if conc >= values[i] and conc < values[i+1]:
			aqi = breakpoints[i] + (conc - values[i])/(values[i+1] - values[i]) * (breakpoints[i+1] - breakpoints[i])
	return aqi



