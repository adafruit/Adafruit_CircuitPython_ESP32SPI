# SPDX-FileCopyrightText: 2021 Adafruit Industries
# SPDX-License-Identifier: MIT

from secrets import secrets  # pylint: disable=no-name-in-module
import board
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket


TIMEOUT = 5
# edit host and port to match server
HOST = "wifitest.adafruit.com"
PORT = 80

# PyPortal or similar; edit pins as needed
spi = board.SPI()
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# connect to wifi AP
esp.connect(secrets)

# test for connectivity to server
print("Server ping:", esp.ping(HOST), "ms")

# create the socket
socket.set_interface(esp)
socketaddr = socket.getaddrinfo(HOST, PORT)[0][4]
s = socket.socket()
s.settimeout(TIMEOUT)

print("Connecting")
s.connect(socketaddr)

print("Sending")
s.send(b"GET /testwifi/index.html HTTP/1.0\r\n\r\n")

print("Receiving")
print(s.recv(1024))
