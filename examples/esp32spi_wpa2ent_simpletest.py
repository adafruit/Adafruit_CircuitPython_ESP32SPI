import time
import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_requests as requests

print("ESP32 SPI WPA2 Enterprise test")

# For running on the PyPortal, use this block
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

# For a board that doesn't have the ESP pin definitions, use this block and
# set the pins as needed.  To connect your board to an ESP32 HUZZAH, here
# are the pin-outs on the HUZZAH32:
# https://learn.adafruit.com/adding-a-wifi-co-processor-to-circuitpython-esp8266-esp32/firmware-files#esp32-only-spi-firmware-3-8
#esp32_cs = DigitalInOut(board.D8)
#esp32_ready = DigitalInOut(board.D5)
#esp32_reset = DigitalInOut(board.D7)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

requests.set_interface(esp)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])

# Set up the SSID you would like to connect to
esp.wifi_set_network(b'YOUR_SSID_HERE')

# If your WPA2 Enterprise network requires an anonymous
# identity to be set, you may set that here
esp.wifi_set_entidentity(b'')

# Set the WPA2 Enterprise username you'd like to use
esp.wifi_set_entusername(b'MY_USERNAME')

# Set the WPA2 Enterprise password you'd like to use
esp.wifi_set_entpassword(b'MY_PASSWORD')

# Once the network settings have been configured,
# we need to enable WPA2 Enterprise mode on the ESP32
esp.wifi_set_entenable()

# Wait for the network to come up
print("Connecting to AP...")
while not esp.is_connected:
    print(".", end = "")
    time.sleep(2)

print("")
print("Connected to", str(esp.ssid, 'utf-8'), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))
print("IP lookup adafruit.com: %s" % esp.pretty_ip(esp.get_host_by_name("adafruit.com")))
print("Ping google.com: %d ms" % esp.ping("google.com"))

print("Done!")
