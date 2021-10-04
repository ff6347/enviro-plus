#!/usr/bin/env python
from twisted.internet import task, reactor
import time
import colorsys
import os
import sys
import ST7735
import requests
import json
import argparse
from dotenv import load_dotenv

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559

    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError as pmsReadTimeoutError
from enviroplus import gas
from subprocess import PIPE, Popen
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import logging

load_dotenv()  # take environment variables from .env.

auth_token = os.getenv("AUTH_TOKEN")

parser = argparse.ArgumentParser(description="run enviro+ and post to stadtpuls.com")
parser.add_argument("--host", nargs="?", type=str, default="http://localhost:4000")

args = parser.parse_args()

host = args.host


logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.info(
    """all-in-one.py - Displays readings from all of Enviro plus' sensors

Press Ctrl+C to exit!

"""
)

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# PMS5003 particulate sensor
pms5003 = PMS5003()

# Create ST7735 LCD display class
st7735 = ST7735.ST7735(
    port=0, cs=1, dc=9, backlight=12, rotation=270, spi_speed_hz=10000000
)

# Initialize display
st7735.begin()

WIDTH = st7735.width
HEIGHT = st7735.height
# Tuning factor for compensation. Decrease this number to adjust the
# temperature down, and increase to adjust up
factor = 0.8

# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    process = Popen(["vcgencmd", "measure_temp"], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index("=") + 1 : output.rindex("'")])


cpu_temps = [get_cpu_temperature()] * 5

delay = 0.5  # Debounce the proximity tap
mode = 0  # The starting mode
last_page = 0
light = 1

sensor_ids = {
    "temp": 5,
    "humidity": 6,
    "pressure": 7,
    "light": 8,
    "ox": 9,
    "red": 10,
    "nh3": 11,
    "pm1": 12,
    "pm25": 13,
    "pm10": 14,
}


def calc_average(lst):
    """
    Driver Code

    lst = [15, 9, 55, 41, 35, 20, 62, 49]

    average = calc_average(lst)
    """
    return sum(lst) / len(lst)


# Create a values dict to store the data
variables = [
    "temperature",
    "pressure",
    "humidity",
    "light",
    "oxidised",
    "reduced",
    "nh3",
    "pm1",
    "pm25",
    "pm10",
]

values = {}

for v in variables:
    values[v] = [1] * WIDTH
# Set up canvas and font
img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
path = os.path.dirname(os.path.realpath(__file__))
font = ImageFont.truetype(path + "/fonts/Asap/Asap-Bold.ttf", 20)

message = ""

# The position of the top bar
top_pos = 25


# Displays data and text on the 0.96" LCD
def display_text(variable, data, unit):
    # Maintain length of list
    values[variable] = values[variable][1:] + [data]
    # Scale the values for the variable between 0 and 1
    colours = [
        (v - min(values[variable]) + 1)
        / (max(values[variable]) - min(values[variable]) + 1)
        for v in values[variable]
    ]
    # Format the variable name and value
    # message = "{}: {:.1f} {}".format(variable[:4], data, unit)
    # logging.info(message)
    draw.rectangle((0, 0, WIDTH, HEIGHT), (255, 255, 255))
    for i in range(len(colours)):
        # Convert the values to colours from red to blue
        colour = (1.0 - colours[i]) * 0.6
        r, g, b = [int(x * 255.0) for x in colorsys.hsv_to_rgb(colour, 1.0, 1.0)]
        # Draw a 1-pixel wide rectangle of colour
        draw.rectangle((i, top_pos, i + 1, HEIGHT), (r, g, b))
        # Draw a line graph in black
        line_y = HEIGHT - (top_pos + (colours[i] * (HEIGHT - top_pos))) + top_pos
        draw.rectangle((i, line_y, i + 1, line_y + 1), (0, 0, 0))
    # Write the text at the top in black
    draw.text((0, 0), message, font=font, fill=(0, 0, 0))
    st7735.display(img)


def get_temperature(log=False):
    # variable = "temperature"
    global cpu_temps
    unit = "C"
    cpu_temp = get_cpu_temperature()
    # Smooth out with some averaging to decrease jitter
    cpu_temps = cpu_temps[1:] + [cpu_temp]
    avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
    raw_temp = bme280.get_temperature()
    data = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
    # message = "{}: {:.1f} {}".format(variable[:4], data, unit)
    # logging.info(message)
    if log == True:
        logging.info("temperature {} {}".format(data, unit))
    # display_text("temperature", data, unit)
    return (data, unit)


def get_pressure(log=False):
    # variable = "pressure"
    unit = "hPa"
    data = bme280.get_pressure()
    if log == True:
        logging.info("pressure {} {}".format(data, unit))
    # display_text("pressure", data, unit)
    return (data, unit)


def get_humidity(log=False):
    # variable = "humidity"
    unit = "%"
    data = bme280.get_humidity()
    if log == True:
        logging.info("humidity {} {}".format(data, unit))
    # display_text("humidity", data, unit)
    return (data, unit)


def get_light(log=False):
    # variable = "light"
    unit = "Lux"
    proximity = ltr559.get_proximity()
    if proximity < 10:
        data = ltr559.get_lux()
    else:
        data = 1
    if log == True:
        logging.info("light {} {}".format(data, unit))
    # display_text("light", data, unit)
    return (data, unit)


def get_oxidised(log=False):

    # variable = "oxidised"
    unit = "kO"
    data = gas.read_all()
    data = data.oxidising / 1000
    if log == True:
        logging.info("oxidised {} {}".format(data, unit))
    # display_text("oxidised", data, unit)
    return (data, unit)


def get_reduced(log=False):
    # variable = "reduced"
    unit = "kO"
    data = gas.read_all()
    data = data.reducing / 1000
    if log == True:
        logging.info("reduced {} {}".format(data, unit))
    # display_text("reduced", data, unit)
    return (data, unit)


def get_nh3(log=False):
    # variable = "nh3"
    unit = "kO"
    data = gas.read_all()
    data = data.nh3 / 1000
    if log == True:
        logging.info("nh3 {} {}".format(data, unit))
    # display_text("nh3", data, unit)
    return (data, unit)


def get_pm1(log=False):
    # variable = "pm1"
    unit = "ug/m3"
    try:
        data = pms5003.read()
    except pmsReadTimeoutError:
        logging.warn("Failed to read PMS5003")
    else:
        data = float(data.pm_ug_per_m3(1.0))
        if log == True:
            logging.info("pm1 {} {}".format(data, unit))
        # display_text("pm1", data, unit)
        return (data, unit)


def get_pm25(log=False):
    # variable = "pm25"
    unit = "ug/m3"
    try:
        data = pms5003.read()
    except pmsReadTimeoutError:
        logging.warn("Failed to read PMS5003")
    else:
        data = float(data.pm_ug_per_m3(2.5))
        if log == True:
            logging.info("pm25 {} {}".format(data, unit))
        # display_text("pm25", data, unit)
        return (data, unit)


def get_pm10(log=False):
    # variable = "pm10"
    unit = "ug/m3"
    try:
        data = pms5003.read()
    except pmsReadTimeoutError:
        logging.warn("Failed to read PMS5003")
    else:
        data = float(data.pm_ug_per_m3(10))
        if log == True:
            logging.info("pm10 {} {}".format(data, unit))
        # display_text("pm10", data, unit)
        return (data, unit)


temp_list = []
press_list = []
hum_list = []
light_list = []
ox_list = []
red_list = []
nh3_list = []
pm1_list = []
pm25_list = []
pm10_list = []


def post_data(payload, sensor_key):
    sensor_id = sensor_ids[sensor_key]
    url = "{}/api/v3/sensors/{}/records".format(host, sensor_id)
    headers = {"authorization": "Bearer {}".format(auth_token)}

    r = requests.post(url, json={"measurements": [payload]}, headers=headers)
    if r.status_code != 201:
        logging.error(
            "{}, Failed to post data to {}: {}".format(r.status_code, host, r.text)
        )


# def post_data(payload, type):
#     query = """mutation insert($payload: Payload!, $type: String!){
#     insertData(payload: $payload, type: $type) {
#     results {
#       name
#       status
#       species
#       type
#       gender
#     }
#     }
#     }"""
#     variables = {"payload": payload, "type": type}
#     print(payload, type)
#     r = requests.post(url, json={"query": query, "variables": variables})
#     print(r.status_code)
#     print(r.text)


def do_averaging():
    global temp_list
    global hum_list
    global hum_list
    global light_list
    global ox_list
    global red_list
    global nh3_list
    global pm1_list
    global pm25_list
    global pm10_list
    logging.info("temp average {:10.2f}{}".format(calc_average(temp_list), "C"))
    post_data(calc_average(temp_list), "temp")
    temp_list.clear()

    logging.info("hum  average {:10.2f}{}".format(calc_average(hum_list), "%"))
    post_data(calc_average(hum_list), "humidity")
    hum_list.clear()

    logging.info("press  average {:10.2f}{}".format(calc_average(press_list), "hPa"))
    post_data(calc_average(press_list), "pressure")
    press_list.clear()

    logging.info("light average {:10.2f}{}".format(calc_average(light_list), "Lux"))
    post_data(calc_average(light_list), "light")
    light_list.clear()

    logging.info("ox average {:10.2f}{}".format(calc_average(ox_list), "kO"))
    post_data(calc_average(ox_list), "ox")
    ox_list.clear()

    logging.info("red average {:10.2f}{}".format(calc_average(red_list), "kO"))
    post_data(calc_average(red_list), "red")
    red_list.clear()

    logging.info("nh3 average {:10.2f}{}".format(calc_average(nh3_list), "kO"))
    post_data(calc_average(nh3_list), "nh3")
    nh3_list.clear()

    logging.info("pm1 average {:10.2f}{}".format(calc_average(pm1_list), "ug/m3"))
    post_data(calc_average(pm1_list), "pm1")
    pm1_list.clear()

    logging.info("pm 2.5 average {:10.2f}{}".format(calc_average(pm25_list), "ug/m3"))
    post_data(calc_average(pm25_list), "pm25")
    pm25_list.clear()

    logging.info("pm10 average {:10.2f}{}".format(calc_average(pm10_list), "ug/m3"))
    post_data(calc_average(pm10_list), "pm10")
    pm10_list.clear()

    # do work here


def do_collecting():
    global temp_list
    global press_list
    global hum_list
    global light_list
    global ox_list
    global red_list
    global nh3_list
    global pm1_list
    global pm25_list
    global pm10_list
    temp = get_temperature()
    temp_list.append(temp[0])
    press = get_pressure()
    press_list.append(press[0])
    hum = get_humidity()
    hum_list.append(hum[0])
    light = get_light()
    light_list.append(light[0])
    ox = get_oxidised()
    ox_list.append(ox[0])
    red = get_reduced()
    red_list.append(red[0])
    nh3 = get_nh3()
    nh3_list.append(nh3[0])
    pm1 = get_pm1()
    pm1_list.append(pm1[0])
    pm25 = get_pm25()
    pm25_list.append(pm25[0])
    pm10 = get_pm10()
    pm10_list.append(pm10[0])


# The main loop
try:
    # while True:
    #     temp = get_temperature()
    #     temp_list.append(temp[0])
    #     press = get_pressure()
    #     press_list.append(press[0])
    #     hum = get_humidity()
    #     hum_list.append(hum[0])
    #     light = get_light()
    #     light_list.append(light[0])
    #     ox = get_oxidised()
    #     ox_list.append(ox[0])
    #     red = get_reduced()
    #     red_list.append(red[0])
    #     nh3 = get_nh3()
    #     nh3_list.append(nh3[0])
    #     pm1 = get_pm1()
    #     pm1_list.append(pm1[0])
    #     pm25 = get_pm25()
    #     pm25_list.append(pm25[0])
    #     pm10 = get_pm10()
    #     pm10_list.append(pm10[0])

    collection_schedule = task.LoopingCall(do_collecting)
    posting_schedule = task.LoopingCall(do_averaging)
    collection_schedule.start(10.0)  # call every 10 seconds
    posting_schedule.start(180.0)  # call every 180 seconds

    reactor.run()

# Exit cleanly
except KeyboardInterrupt:
    sys.exit(0)
