# SPDX-FileCopyrightText: 2021 Adafruit Industries
# SPDX-License-Identifier: MIT

import struct
import time
import board
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

TIMEOUT = 5
# edit host and port to match server
HOST = "pool.ntp.org"
PORT = 123
NTP_TO_UNIX_EPOCH = 2208988800  # 1970-01-01 00:00:00

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
s = socket.socket(type=socket.SOCK_DGRAM)

s.settimeout(TIMEOUT)

print("Sending")
s.connect(socketaddr, conntype=esp.UDP_MODE)
packet = bytearray(48)
packet[0] = 0b00100011  # Not leap second, NTP version 4, Client mode
s.send(packet)

print("Receiving")
packet = s.recv(48)
seconds = struct.unpack_from("!I", packet, offset=len(packet) - 8)[0]
print("Time:", time.localtime(seconds - NTP_TO_UNIX_EPOCH))
