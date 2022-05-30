# SPDX-FileCopyrightText: 2020 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import gc
import struct
import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("ESP32 SPI socket count server test")

NO_SOCK_AVAIL = const(255)

esp32_cs = DigitalInOut(board.GP10)
esp32_ready = DigitalInOut(board.GP9)
esp32_reset = DigitalInOut(board.GP8)
spi = busio.SPI(board.GP14, board.GP11, board.GP12)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)


PORT = 8981

# connect to wifi AP
esp.connect(secrets)

# create the socket
socket.set_interface(esp)


class CountServer:
    """Server to return counts"""

    def __init__(self):
        self._server_sock = socket.socket(socknum=NO_SOCK_AVAIL)
        self._client_sock = socket.socket(socknum=NO_SOCK_AVAIL)
        self._counter = 0
        self.port = PORT
        self._debug = 3

    def start(self):
        """
        starts the server and begins listening for incoming connections.
        Call update_poll in the main loop for the application callable to be
        invoked on receiving an incoming request.
        """
        self._server_sock = socket.socket()
        esp.start_server(self.port, self._server_sock.socknum)
        ip = esp.pretty_ip(esp.ip_address)
        print("Server available at {0}:{1}".format(ip, self.port))
        print(
            "Server status: ",
            esp.server_state(self._server_sock.socknum),
        )

    def client_available(self):
        """
        returns a client socket connection if available.
        Otherwise, returns None
        :return: the client
        :rtype: Socket
        """
        sock = None
        if self._server_sock.socknum == NO_SOCK_AVAIL:
            raise ValueError("Server has not been started, cannot check for clients!")

        if self._client_sock.socknum != NO_SOCK_AVAIL:
            # check previous received client socket
            if self._debug > 2:
                print("checking if last client sock still valid")
            if self._client_sock.connected() and self._client_sock.available():
                sock = self._client_sock
        if not sock:
            # check for new client sock
            if self._debug > 3:
                print("checking for new client sock")
            client_sock_num = esp.socket_available(self._server_sock.socknum)
            sock = socket.socket(socknum=client_sock_num)

        if sock and sock.socknum != NO_SOCK_AVAIL:
            if self._debug > 2:
                print("client sock num is: ", sock.socknum)
            self._client_sock = sock
            return self._client_sock

        return None

    def response(self):
        current = self._counter
        self._counter += 1
        print(f"Sending {current}")
        return struct.pack("!I", current)

    def run(self):
        """
        Call this method inside your main event loop to get the server
        check for new incoming client requests.
        """
        while True:
            self.client_available()
            if self._client_sock and self._client_sock.available():
                result = self.response()
                try:
                    self._client_sock.send(result)
                    gc.collect()
                finally:
                    if self._debug > 3:
                        print("closing")
                    self._client_sock.close()


cs = CountServer()
cs.start()
cs.run()
