import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_wifimanager as wifimanager
import adafruit_esp32spi.adafruit_esp32spi_server as server

import neopixel


# This example depends on the 'static' folder in the examples folder
# being copied to the root of the circuitpython filesystem. 
# This is where our static assets like html, js, and css live.


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

try:
    import json as json_module
except ImportError:
    import ujson as json_module

print("ESP32 SPI simple web server test!")

esp32_cs = DigitalInOut(board.D10)
esp32_ready = DigitalInOut(board.D9)
esp32_reset = DigitalInOut(board.D7)
esp32_gpio0 = DigitalInOut(board.D12)

"""Use below for Most Boards"""
status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2) # Uncomment for Most Boards
"""Uncomment below for ItsyBitsy M4"""
# import adafruit_dotstar as dotstar
# status_light = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=1)


spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(
    spi, esp32_cs, esp32_ready, esp32_reset, gpio0_pin=esp32_gpio0, debug=False)

## Connect to wifi with secrets
wifi = wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light, debug=True)
wifi.connect()

server.set_interface(esp)
server = server.server(80, debug=False)


def onLedHigh(headers, body, client): # pylint: disable=unused-argument
    print("led on!")
    status_light.fill((0, 0, 100))
    server.serve_file("static/index.html")

def onLedLow(headers, body, client): # pylint: disable=unused-argument
    print("led off!")
    status_light.fill(0)
    server.serve_file("static/index.html")

def onLedColor(headers, body, client): # pylint: disable=unused-argument
    rgb = json_module.loads(body)
    print("led color: " + rgb)
    status_light.fill((rgb.get("r"), rgb.get("g"), rgb.get("b")))
    client.write(b"HTTP/1.1 200 OK")
    client.close()

server.set_static_dir("/static")
server.on("GET", "/H", onLedHigh)
server.on("GET", "/L", onLedLow)
server.on("POST", "/ajax/ledcolor", onLedColor)


print("open this IP in your browser: ", esp.pretty_ip(esp.ip_address))

server.start()

while True:
    server.update_poll()
