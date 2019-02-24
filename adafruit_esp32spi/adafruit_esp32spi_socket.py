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
`adafruit_esp32spi_socket`
================================================================================

A socket compatible interface thru the ESP SPI command set

* Author(s): ladyada
"""


import time
import gc
from micropython import const

_the_interface = None   # pylint: disable=invalid-name
def set_interface(iface):
    """Helper to set the global internet interface"""
    global _the_interface   # pylint: disable=global-statement, invalid-name
    _the_interface = iface

SOCK_STREAM = const(1)
AF_INET = const(2)

MAX_PACKET = const(4000)

# pylint: disable=too-many-arguments, unused-argument
def getaddrinfo(host, port, family=0, socktype=0, proto=0, flags=0):
    """Given a hostname and a port name, return a 'socket.getaddrinfo'
    compatible list of tuples. Honestly, we ignore anything but host & port"""
    if not isinstance(port, int):
        raise RuntimeError("Port must be an integer")
    ipaddr = _the_interface.get_host_by_name(host)
    return [(AF_INET, socktype, proto, '', (ipaddr, port))]
# pylint: enable=too-many-arguments, unused-argument

# pylint: disable=unused-argument, redefined-builtin, invalid-name
class socket:
    """A simplified implementation of the Python 'socket' class, for connecting
    through an interface to a remote device"""
    def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, fileno=None):
        if family != AF_INET:
            raise RuntimeError("Only AF_INET family supported")
        if type != SOCK_STREAM:
            raise RuntimeError("Only SOCK_STREAM type supported")
        self._buffer = b''
        self._socknum = _the_interface.get_socket()
        self.settimeout(0)

    def connect(self, address, conntype=None):
        """Connect the socket to the 'address' (which can be 32bit packed IP or
        a hostname string). 'conntype' is an extra that may indicate SSL or not,
        depending on the underlying interface"""
        host, port = address
        if not _the_interface.socket_connect(self._socknum, host, port, conn_mode=conntype):
            raise RuntimeError("Failed to connect to host", host)
        self._buffer = b''

    def write(self, data):         # pylint: disable=no-self-use
        """Send some data to the socket"""
        _the_interface.socket_write(self._socknum, data)
        gc.collect()

    def readline(self):
        """Attempt to return as many bytes as we can up to but not including '\r\n'"""
        #print("Socket readline")
        while b'\r\n' not in self._buffer:
            # there's no line already in there, read some more
            avail = min(_the_interface.socket_available(self._socknum), MAX_PACKET)
            if avail:
                self._buffer += _the_interface.socket_read(self._socknum, avail)
        firstline, self._buffer = self._buffer.split(b'\r\n', 1)
        gc.collect()
        return firstline

    def read(self, size=0):
        """Read up to 'size' bytes from the socket, this may be buffered internally!
        If 'size' isnt specified, return everything in the buffer."""
        #print("Socket read", size)
        if size == 0:   # read as much as we can at the moment
            while True:
                avail = min(_the_interface.socket_available(self._socknum), MAX_PACKET)
                if avail:
                    self._buffer += _the_interface.socket_read(self._socknum, avail)
                else:
                    break
            gc.collect()
            ret = self._buffer
            self._buffer = b''
            gc.collect()
            return ret
        stamp = time.monotonic()

        to_read = size - len(self._buffer)
        received = []
        while to_read > 0:
            #print("Bytes to read:", to_read)
            avail = min(_the_interface.socket_available(self._socknum), MAX_PACKET)
            if avail:
                stamp = time.monotonic()
                recv = _the_interface.socket_read(self._socknum, min(to_read, avail))
                received.append(recv)
                to_read -= len(recv)
                gc.collect()
            if time.monotonic() - stamp > self._timeout:
                break
        #print(received)
        self._buffer += b''.join(received)

        ret = None
        if len(self._buffer) == size:
            ret = self._buffer
            self._buffer = b''
        else:
            ret = self._buffer[:size]
            self._buffer = self._buffer[size:]
        gc.collect()
        return ret

    def settimeout(self, value):
        """Set the read timeout for sockets, if value is 0 it will block"""
        self._timeout = value

    def close(self):
        """Close the socket, after reading whatever remains"""
        _the_interface.socket_close(self._socknum)
# pylint: enable=unused-argument, redefined-builtin, invalid-name
