# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from digitalio import DigitalInOut

import neopixel
import adafruit_fancyled.adafruit_fancyled as fancy

from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("ESP32 SPI webclient test")

DATA_SOURCE = "https://api.thingspeak.com/channels/1417/feeds.json?results=1"
DATA_LOCATION = ["feeds", 0, "field2"]

esp32_cs = DigitalInOut(board.D9)
esp32_ready = DigitalInOut(board.D10)
esp32_reset = DigitalInOut(board.D5)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
"""Use below for Most Boards"""
status_light = neopixel.NeoPixel(
    board.NEOPIXEL, 1, brightness=0.2
)  # Uncomment for Most Boards
"""Uncomment below for ItsyBitsy M4"""
# status_light = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=0.2)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

# neopixels
pixels = neopixel.NeoPixel(board.A1, 16, brightness=0.3)
pixels.fill(0)

# we'll save the value in question
last_value = value = None

while True:
    try:
        print("Fetching json from", DATA_SOURCE)
        response = wifi.get(DATA_SOURCE)
        print(response.json())
        value = response.json()
        for key in DATA_LOCATION:
            value = value[key]
            print(value)
        response.close()
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        wifi.reset()
        continue

    if not value:
        continue
    if last_value != value:
        color = int(value[1:], 16)
        red = color >> 16 & 0xFF
        green = color >> 8 & 0xFF
        blue = color & 0xFF
        gamma_corrected = fancy.gamma_adjust(fancy.CRGB(red, green, blue)).pack()

        pixels.fill(gamma_corrected)
        last_value = value
    response = None
    time.sleep(60)
