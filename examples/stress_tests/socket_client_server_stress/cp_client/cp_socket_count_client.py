# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import struct
import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("ESP32 SPI socket count client test")

TIMEOUT = 5
# edit host and port to match server
HOST = "192.168.1.149"
PORT = 8981

esp32_cs = DigitalInOut(board.GP10)
esp32_ready = DigitalInOut(board.GP9)
esp32_reset = DigitalInOut(board.GP8)
spi = busio.SPI(board.GP14, board.GP11, board.GP12)
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


while True:
  print("Connecting")
  s.connect(socketaddr)
  # get a count from the Socket. lets receive this as 4 bytes - unpack as an int.
  data = s.recv(4)
  # print it
  print(f"Data length {len(data)}. Data: ", end='')
  print(struct.unpack("!I", data))
  time.sleep(0.01)
  s.close()