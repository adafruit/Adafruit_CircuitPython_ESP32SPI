# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Example code implementing WPA2 Enterprise mode
#
# This code requires firmware version 1.3.0, or newer, running
# on the ESP32 WiFi co-processor. The latest firmware, and wiring
# info if you are using something other than a PyPortal, can be found
# in the Adafruit Learning System:
# https://learn.adafruit.com/adding-a-wifi-co-processor-to-circuitpython-esp8266-esp32/firmware-files#esp32-only-spi-firmware-3-8

import re
import time
import board
import busio
from digitalio import DigitalInOut

import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi

# Version number comparison code. Credit to gnud on stackoverflow
# (https://stackoverflow.com/a/1714190), swapping out cmp() to
# support Python 3.x and thus, CircuitPython
def version_compare(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r"(\.0+)*$", "", v).split(".")]

    return (normalize(version1) > normalize(version2)) - (
        normalize(version1) < normalize(version2)
    )


print("ESP32 SPI WPA2 Enterprise test")

# ESP32 setup
# If your board does define the three pins listed below,
# you can set the correct pins in the second block
try:
    esp32_cs = DigitalInOut(board.ESP_CS)
    esp32_ready = DigitalInOut(board.ESP_BUSY)
    esp32_reset = DigitalInOut(board.ESP_RESET)
except AttributeError:
    esp32_cs = DigitalInOut(board.D9)
    esp32_ready = DigitalInOut(board.D10)
    esp32_reset = DigitalInOut(board.D5)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

requests.set_socket(socket, esp)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")

# Get the ESP32 fw version number, remove trailing byte off the returned bytearray
# and then convert it to a string for prettier printing and later comparison
firmware_version = "".join([chr(b) for b in esp.firmware_version[:-1]])
print("Firmware vers.", firmware_version)

print("MAC addr:", [hex(i) for i in esp.MAC_address])

# WPA2 Enterprise support was added in fw ver 1.3.0. Check that the ESP32
# is running at least that version, otherwise, bail out
assert (
    version_compare(firmware_version, "1.3.0") >= 0
), "Incorrect ESP32 firmware version; >= 1.3.0 required."

# Set up the SSID you would like to connect to
# Note that we need to call wifi_set_network prior
# to calling wifi_set_enable.
esp.wifi_set_network(b"YOUR_SSID_HERE")

# If your WPA2 Enterprise network requires an anonymous
# identity to be set, you may set that here
esp.wifi_set_entidentity(b"")

# Set the WPA2 Enterprise username you'd like to use
esp.wifi_set_entusername(b"MY_USERNAME")

# Set the WPA2 Enterprise password you'd like to use
esp.wifi_set_entpassword(b"MY_PASSWORD")

# Once the network settings have been configured,
# we need to enable WPA2 Enterprise mode on the ESP32
esp.wifi_set_entenable()

# Wait for the network to come up
print("Connecting to AP...")
while not esp.is_connected:
    print(".", end="")
    time.sleep(2)

print("")
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))
print(
    "IP lookup adafruit.com: %s" % esp.pretty_ip(esp.get_host_by_name("adafruit.com"))
)
print("Ping google.com: %d ms" % esp.ping("google.com"))

print("Done!")
