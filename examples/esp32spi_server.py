import board
import busio
from digitalio import DigitalInOut
from secrets import secrets

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_wifimanager as wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket

print("ESP32 SPI web server test!!!!!!")

esp32_cs = DigitalInOut(board.D10)
esp32_ready = DigitalInOut(board.D9)
esp32_reset = DigitalInOut(board.D7)


spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset, debug=True)

wifi = wifimanager.ESPSPI_WiFiManager(esp, secrets, debug=True)

wifi.create_ap()
time.sleep(10)

sock = socket.socket() # gets and creates a socket
sock_num = sock.get_sock_num() # returns socket number

esp.start_server(sock_num, 80)
print("socket num: ", sock_num)
print("socket status?: ", esp.socket_status(sock_num))
print("IP addr: ", esp.pretty_ip(esp.ip_address))

status = 0
while True:
    if status != esp.status:
        status = esp.status

        if status == 8:
            print("Device connected!") ## works
        else:
            print("Device disconnected status=", status) ## works

    print("socket available?: ", esp.socket_available(sockNum))
    print("socket_status: ", esp.socket_status(sockNum))
    print(sock.read())


print("done!")
