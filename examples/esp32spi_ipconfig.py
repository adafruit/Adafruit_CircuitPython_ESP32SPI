# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

HOSTNAME = "esp32-spi-hostname-test"

IP_ADDRESS = "192.168.1.111"
GATEWAY_ADDRESS = "192.168.1.1"
SUBNET_MASK = "255.255.255.0"

UDP_IN_ADDR = "192.168.1.1"
UDP_IN_PORT = 5500

UDP_TIMEOUT = 20

esp32_cs = DigitalInOut(board.CS1)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK1, board.MOSI1, board.MISO1)

esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
socket.set_interface(esp)

s_in = socket.socket(type=socket.SOCK_DGRAM)
s_in.settimeout(UDP_TIMEOUT)
print("set hostname:", HOSTNAME)
esp.set_hostname(HOSTNAME)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
ip1 = esp.ip_address

print("set ip dns")
esp.set_dns_config("192.168.1.1", "8.8.8.8")

print("set ip config")
esp.set_ip_config(IP_ADDRESS, GATEWAY_ADDRESS, SUBNET_MASK)

time.sleep(1)
ip2 = esp.ip_address

time.sleep(1)
info = esp.network_data
print(
    "get network_data: ",
    esp.pretty_ip(info["ip_addr"]),
    esp.pretty_ip(info["gateway"]),
    esp.pretty_ip(info["netmask"]),
)

IP_ADDR = esp.pretty_ip(esp.ip_address)
print("ip:", IP_ADDR)
print("My IP address is", esp.pretty_ip(esp.ip_address))
print("udp in addr: ", UDP_IN_ADDR, UDP_IN_PORT)

socketaddr_udp_in = socket.getaddrinfo(UDP_IN_ADDR, UDP_IN_PORT)[0][4]
s_in.connect(socketaddr_udp_in, conntype=esp.UDP_MODE)
print("connected local UDP")

while True:
    data = s_in.recv(1205)
    if len(data) >= 1:
        data = data.decode("utf-8")
        print(len(data), data)
