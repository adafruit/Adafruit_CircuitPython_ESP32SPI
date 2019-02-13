import time
import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_requests as requests

import neopixel
import adafruit_fancyled.adafruit_fancyled as fancy



# Get wifi details and more from a settings.py file
try:
    from esp32spi_settings import settings
except ImportError:
    print("WiFi settings are kept in settings.py, please add them there!")
    raise



print("ESP32 SPI webclient test")

DATA_SOURCE = "https://api.thingspeak.com/channels/1417/feeds.json?results=1"
DATA_LOCATION = ["feeds", 0, "field2"]


esp32_cs = DigitalInOut(board.D9)
esp32_ready = DigitalInOut(board.D10)
esp32_reset = DigitalInOut(board.D5)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

requests.set_interface(esp)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])
for ap in esp.scan_networks():
    print("\t%s\t\tRSSI: %d" % (str(ap['ssid'], 'utf-8'), ap['rssi']))
while not esp.is_connected:
    try:
        print("Connecting to AP...")
        esp.connect_AP(bytes(settings['ssid'],'utf-8'), bytes(settings['password'],'utf-8'))
    except (ValueError, RuntimeError) as e:
        print("Failed to connect, retrying\n", e)
        continue
print("Connected to", str(esp.ssid, 'utf-8'), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))


# neopixels
pixels = neopixel.NeoPixel(board.A1, 16, brightness=0.3)
pixels.fill(0)
builtin = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)
builtin[0] = 0

# we'll save the value in question
last_value = value = None
the_time = None
times = 0


while True:
    try:
        while not esp.is_connected:
            builtin[0] = (100, 0, 0)
            # settings dictionary must contain 'ssid' and 'password' at a minimum
            esp.connect_AP(bytes(settings['ssid'],'utf-8'), bytes(settings['password'],'utf-8'))
        builtin[0] = (0, 100, 0)
        print("Fetching json from", DATA_SOURCE)
        builtin[0] = (100, 100, 0)
        r = requests.get(DATA_SOURCE)
        builtin[0] = (0, 0, 100)
        print(r.json())
        value=r.json()
        for x in DATA_LOCATION:
            value = value[x]
            print(value)
        r.close()
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        continue

    builtin[0] = (100, 100, 100)
    if not value:
        continue
    if last_value != value:
        color = int(value[1:],16)
        red = color >> 16 & 0xFF
        green = color >> 8 & 0xFF
        blue = color& 0xFF
        gamma_corrected = fancy.gamma_adjust(fancy.CRGB(red, green, blue)).pack()

        pixels.fill(gamma_corrected)
        last_value = value
    times += 1
    r = None
    time.sleep(60)
