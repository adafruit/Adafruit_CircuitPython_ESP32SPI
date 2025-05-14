# SPDX-FileCopyrightText: 2021 Adafruit Industries
# SPDX-License-Identifier: MIT

from os import getenv

import board
import busio
from digitalio import DigitalInOut

import adafruit_esp32spi.adafruit_esp32spi_socketpool as socketpool
from adafruit_esp32spi import adafruit_esp32spi

# Get wifi details and more from a settings.toml file
# tokens used by this Demo: CIRCUITPY_WIFI_SSID, CIRCUITPY_WIFI_PASSWORD
ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")

TIMEOUT = 5
# edit host and port to match server
HOST = "wifitest.adafruit.com"
PORT = 80

# Secondary (SCK1) SPI used to connect to WiFi board on Arduino Nano Connect RP2040
if "SCK1" in dir(board):
    spi = busio.SPI(board.SCK1, board.MOSI1, board.MISO1)
elif "SPI" in dir(board):
    spi = board.SPI()
else:
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
# PyPortal or similar; edit pins as needed
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# connect to wifi AP
esp.connect(ssid, password)

# test for connectivity to server
print("Server ping:", esp.ping(HOST), "ms")

# create the socket
pool = socketpool.SocketPool(esp)
socketaddr = pool.getaddrinfo(HOST, PORT)[0][4]
s = pool.socket()
s.settimeout(TIMEOUT)

print("Connecting")
s.connect(socketaddr)

print("Sending")
s.send(b"GET /testwifi/index.html HTTP/1.0\r\n\r\n")

print("Receiving")
print(s.recv(1024))
