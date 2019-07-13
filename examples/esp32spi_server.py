import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_wifimanager as wifimanager
import adafruit_esp32spi.adafruit_esp32spi_server as server

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("ESP32 SPI simple web server test!")

esp32_cs = DigitalInOut(board.D10)
esp32_ready = DigitalInOut(board.D9)
esp32_reset = DigitalInOut(board.D7)
esp32_gpio0 = DigitalInOut(board.D12)


spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset, gpio0_pin=esp32_gpio0, debug=False)

## Connect to wifi with secrets
wifi = wifimanager.ESPSPI_WiFiManager(esp, secrets, debug=True)
wifi.connect()

server.set_interface(esp)
server = server.server(80, True)
server.start()

print("IP addr: ", esp.pretty_ip(esp.ip_address))
print("server started!")


while True:

    client = server.client_available()
    if (client.available()):
        data = client.read()
        if len(data):
            print(data)
            client.write(b"HTTP/1.1 200 OK\r\n")
            client.write(b"Content-type:text/html\r\n")
            client.write(b"\r\n")

            client.write(b"Click <a href=\"/H\">here</a> turn the LED on!!!<br>\r\n")
            client.write(b"Click <a href=\"/L\">here</a> turn the LED off!!!!<br>\r\n")

            client.write(b"\r\n")
            client.close()
