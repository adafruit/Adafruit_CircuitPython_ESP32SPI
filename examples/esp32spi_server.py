import board
import busio
from digitalio import DigitalInOut
from secrets import secrets

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_wifimanager as wifimanager

print("ESP32 SPI web server test!!!!!!")

esp32_cs = DigitalInOut(board.D10)
esp32_ready = DigitalInOut(board.D9)
esp32_reset = DigitalInOut(board.D7)


spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset, debug=True)

wifi = wifimanager.ESPSPI_WiFiManager(esp, secrets, debug=True)

wifi.create_ap();

print("done!")
