# The MIT License (MIT)
#
# Copyright (c) 2019 ladyada for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
`adafruit_esp32spi_server`
================================================================================

TODO: better description?
Server management lib to make handling and responding to incoming requests much easier

* Author(s): Matt Costi
"""

from micropython import const
import adafruit_esp32spi_socket as socket

_the_interface = None   # pylint: disable=invalid-name
def set_interface(iface):
    """Helper to set the global internet interface"""
    global _the_interface   # pylint: disable=global-statement, invalid-name
    _the_interface = iface
    socket.set_interface(iface)

NO_SOCK_AVAIL = const(255)


# pylint: disable=unused-argument, redefined-builtin, invalid-name
class server:
    """ TODO: class docs """
    def __init__(self, port=80, debug=False):
        self.port = port
        self._server_sock = socket.socket(socknum=NO_SOCK_AVAIL)
        self._client_sock = socket.socket(socknum=NO_SOCK_AVAIL)
        self._debug = debug


    def start(self):
        """ start the server """
        self._server_sock = socket.socket()
        _the_interface.start_server(self.port, self._server_sock.socknum)
        if self._debug:
            ip = _the_interface.pretty_ip(_the_interface.ip_address)
            print("Server available at {0}:{1}".format(ip, self.port))
            print("Sever status: ", _the_interface.get_server_state(self._server_sock.socknum))

    def client_available(self):
        """
        returns a client socket connection if available.otherwise, returns a non available socket
        :return the client
        :rtype Socket
        """
        sock = None
        if self._server_sock.socknum != NO_SOCK_AVAIL:
            if self._client_sock.socknum != NO_SOCK_AVAIL:
                # check previous received client socket
                if self._debug:
                    print("checking if last client sock still valid")
                if self._client_sock.connected() and self._client_sock.available():
                    sock = self._client_sock
            if not sock:
                # check for new client sock
                if self._debug:
                    print("checking for new client sock")
                client_sock_num = _the_interface.socket_available(self._server_sock.socknum)
                sock = socket.socket(socknum=client_sock_num)
        else:
            print("Server has not been started, cannot check for clients!")

        if sock and sock.socknum != NO_SOCK_AVAIL:
            if self._debug:
                print("client sock num is: ", sock.socknum)
            self._client_sock = sock
            return self._client_sock

        return socket.socket(socknum=NO_SOCK_AVAIL)
