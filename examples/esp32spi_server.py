import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_wifimanager as wifimanager
import adafruit_esp32spi.adafruit_esp32spi_server as server

import neopixel

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

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


def onLedHigh(headers, body, client):
    print("led on!")
    print("headers: ", headers)
    print("body: ", body)
    status_light.fill((0, 0, 100))
    respond(headers, body, client)

def onLedLow(headers, body, client):
    print("led off!")
    print("headers: ", headers)
    print("body: ", body)
    status_light.fill(0)
    respond(headers, body, client)

def respond(headers, body, client):
    print("headers: ", headers)
    print("body: ", body)

    client.write(b"HTTP/1.1 200 OK\r\n")
    client.write(b"Content-type:text/html\r\n")
    client.write(b"\r\n")

    client.write(b"Click <a href=\"/H\">here</a> turn the LED on!!!<br>\r\n")
    client.write(b"Click <a href=\"/L\">here</a> turn the LED off!!!!<br>\r\n")

    client.write(b"\r\n")
    client.close()

server.on("GET", "/", respond)
server.on("GET", "/H", onLedHigh)
server.on("GET", "/L", onLedLow)


print("IP addr: ", esp.pretty_ip(esp.ip_address))

server.start()
print("server started!")
while True:
    server.update_poll()
