import time
import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager

print("ESP32 SPI webclient test")

# Get wifi details and more from a settings.py file
try:
    from esp32spi_settings import settings
except ImportError:
    print("WiFi settings are kept in esp32spi_settings.py, please add them there!")
    raise

esp32_cs = DigitalInOut(board.D9)
esp32_ready = DigitalInOut(board.D10)
esp32_reset = DigitalInOut(board.D5)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, settings, board.NEOPIXEL)

counter = 0
while True:
    try:
        print("Posting data...", end='')
        data = counter
        feed = 'test'
        payload = {'value':data}
        response = wifi.post(
            "https://io.adafruit.com/api/v2/"+settings['aio_username']+"/feeds/"+feed+"/data",
            json=payload,headers={bytes("X-AIO-KEY","utf-8"):bytes(settings['aio_key'],"utf-8")})
        print(response.json())
        response.close()
        counter = counter + 1
        print("OK")
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        continue
    response = None
    time.sleep(15)
