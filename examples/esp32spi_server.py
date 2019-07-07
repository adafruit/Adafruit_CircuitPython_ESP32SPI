import board
import busio
import time
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
esp32_gpio0 = DigitalInOut(board.D12)


spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset, gpio0_pin=esp32_gpio0, debug=False)

## Create Access Point from SSID and optional password in secrets
wifi = wifimanager.ESPSPI_WiFiManager(esp, secrets, debug=True)
wifi.create_ap()
time.sleep(10)

socket.set_interface(esp)
sock = socket.socket() # Request a socket for the server
curr_sock = sock
sockNum = sock.get_sock_num()
print("server status: ", esp.get_server_state(sockNum))

# Start the server on port 80 with the socket number we just requested for it.
esp.start_server(80, sockNum)

print("socket num: ", sockNum)
print("server status: ", esp.get_server_state(sockNum))
print("IP addr: ", esp.pretty_ip(esp.ip_address))
print("info: ", esp.network_data)
print("done!")


status = 0
last_sock = 255
def server_avail(): # TODO: make a server helper class
    global last_sock
    sock = 255;

    if (curr_sock != 255):
        # if (last_sock != 255):
        #       TODO: if last sock, check that last_sock is still connected and available
        #     sock = last_sock
        if (sock == 255):
            sock = esp.socket_available(sockNum)
    if (sock != 255):
        last_sock = sock
        return sock

    return 255

while True:
    if status != esp.status: # TODO: Move device connected check to server class ?
        status = esp.status

        if status == 8:
            print("Device connected! status=", status)
        else:
            print("Device disconnected! status=", status)


    avail = server_avail()
    if (avail != 255):
        sock.set_sock_num(avail) # TODO: Server class should return a new client socket
        data = sock.read()
        if (len(data)):
            print(data)
            sock.write(b"HTTP/1.1 200 OK\r\n");
            sock.write(b"Content-type:text/html\r\n");
            sock.write(b"\r\n");

            sock.write(b"Click <a href=\"/H\">here</a> turn the LED on!!!<br>\r\n");
            sock.write(b"Click <a href=\"/L\">here</a> turn the LED off!!!!<br>\r\n");

            sock.write(b"\r\n")
            sock.close()
