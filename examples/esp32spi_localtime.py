import time
import board
import busio
from digitalio import DigitalInOut
import microcontroller
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
import rtc

# Get wifi details and more from a settings.py file
try:
    from settings import settings
except ImportError:
    print("WiFi settings are kept in settings.py, please add them there!")
    raise

print("ESP32 local time")

TIME_API = "http://worldtimeapi.org/api/ip"

esp32_cs = DigitalInOut(microcontroller.pin.PB14) # PB14
esp32_ready = DigitalInOut(microcontroller.pin.PB16)
esp32_gpio0 = DigitalInOut(microcontroller.pin.PB15)
esp32_reset = DigitalInOut(microcontroller.pin.PB17)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, settings, board.NEOPIXEL)

the_rtc = rtc.RTC()

response = None
while True:
    try:
        print("Fetching json from", TIME_API)
        response = wifi.get(TIME_API)
        break
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        continue

json = response.json()
current_time = json['datetime']
the_date, the_time = current_time.split('T')
year, month, mday = [int(x) for x in the_date.split('-')]
the_time = the_time.split('.')[0]
hours, minutes, seconds = [int(x) for x in the_time.split(':')]

# We can also fill in these extra nice things
year_day = json['day_of_year']
week_day = json['day_of_week']
is_dst = json['dst']

now = time.struct_time((year, month, mday, hours, minutes, seconds, week_day, year_day, is_dst))
print(now)
the_rtc.datetime = now

while True:
    print(time.localtime())
    time.sleep(1)
