# SPDX-FileCopyrightText: Copyright (c) 2019 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_esp32spi_socket`
================================================================================

A socket compatible interface thru the ESP SPI command set

* Author(s): ladyada
"""

# pylint: disable=no-name-in-module

import time
import gc
from micropython import const
from adafruit_esp32spi import adafruit_esp32spi

_the_interface = None  # pylint: disable=invalid-name


def set_interface(iface):
    """Helper to set the global internet interface"""
    global _the_interface  # pylint: disable=global-statement, invalid-name
    _the_interface = iface


SOCK_STREAM = const(0)
SOCK_DGRAM = const(1)
AF_INET = const(2)
NO_SOCKET_AVAIL = const(255)

MAX_PACKET = const(4000)

# pylint: disable=too-many-arguments, unused-argument
def getaddrinfo(host, port, family=0, socktype=0, proto=0, flags=0):
    """Given a hostname and a port name, return a 'socket.getaddrinfo'
    compatible list of tuples. Honestly, we ignore anything but host & port"""
    if not isinstance(port, int):
        raise RuntimeError("Port must be an integer")
    ipaddr = _the_interface.get_host_by_name(host)
    return [(AF_INET, socktype, proto, "", (ipaddr, port))]


# pylint: enable=too-many-arguments, unused-argument

# pylint: disable=unused-argument, redefined-builtin, invalid-name
class socket:
    """A simplified implementation of the Python 'socket' class, for connecting
    through an interface to a remote device"""

    # pylint: disable=too-many-arguments
    def __init__(
        self, family=AF_INET, type=SOCK_STREAM, proto=0, fileno=None, socknum=None
    ):
        if family != AF_INET:
            raise RuntimeError("Only AF_INET family supported")
        self._type = type
        self._buffer = b""
        self._socknum = socknum if socknum else _the_interface.get_socket()
        self.settimeout(0)

    # pylint: enable=too-many-arguments

    def connect(self, address, conntype=None):
        """Connect the socket to the 'address' (which can be 32bit packed IP or
        a hostname string). 'conntype' is an extra that may indicate SSL or not,
        depending on the underlying interface"""
        host, port = address
        if conntype is None:
            conntype = _the_interface.TCP_MODE
        if not _the_interface.socket_connect(
            self._socknum, host, port, conn_mode=conntype
        ):
            raise RuntimeError("Failed to connect to host", host)
        self._buffer = b""

    def send(self, data):  # pylint: disable=no-self-use
        """Send some data to the socket."""
        if self._type is SOCK_DGRAM:
            conntype = _the_interface.UDP_MODE
        else:
            conntype = _the_interface.TCP_MODE
        _the_interface.socket_write(self._socknum, data, conn_mode=conntype)
        gc.collect()

    def write(self, data):
        """Sends data to the socket.
        NOTE: This method is deprecated and will be removed.
        """
        self.send(data)

    def readline(self):
        """Attempt to return as many bytes as we can up to but not including '\r\n'"""
        # print("Socket readline")
        stamp = time.monotonic()
        while b"\r\n" not in self._buffer:
            # there's no line already in there, read some more
            avail = self.available()
            if avail:
                self._buffer += _the_interface.socket_read(self._socknum, avail)
            elif self._timeout > 0 and time.monotonic() - stamp > self._timeout:
                self.close()  # Make sure to close socket so that we don't exhaust sockets.
                raise RuntimeError("Didn't receive full response, failing out")
        firstline, self._buffer = self._buffer.split(b"\r\n", 1)
        gc.collect()
        return firstline

    def recv(self, bufsize=0):
        """Reads some bytes from the connected remote address. Will only return
        an empty string after the configured timeout.

        :param int bufsize: maximum number of bytes to receive
        """
        # print("Socket read", bufsize)
        if bufsize == 0:  # read as much as we can at the moment
            while True:
                avail = self.available()
                if avail:
                    self._buffer += _the_interface.socket_read(self._socknum, avail)
                else:
                    break
            gc.collect()
            ret = self._buffer
            self._buffer = b""
            gc.collect()
            return ret
        stamp = time.monotonic()

        to_read = bufsize - len(self._buffer)
        received = []
        while to_read > 0:
            # print("Bytes to read:", to_read)
            avail = self.available()
            if avail:
                stamp = time.monotonic()
                recv = _the_interface.socket_read(self._socknum, min(to_read, avail))
                received.append(recv)
                to_read -= len(recv)
                gc.collect()
            elif received:
                # We've received some bytes but no more are available. So return
                # what we have.
                break
            if self._timeout > 0 and time.monotonic() - stamp > self._timeout:
                break
        # print(received)
        self._buffer += b"".join(received)

        ret = None
        if len(self._buffer) == bufsize:
            ret = self._buffer
            self._buffer = b""
        else:
            ret = self._buffer[:bufsize]
            self._buffer = self._buffer[bufsize:]
        gc.collect()
        return ret

    def read(self, size=0):
        """Read up to 'size' bytes from the socket, this may be buffered internally!
        If 'size' isnt specified, return everything in the buffer.
        NOTE: This method is deprecated and will be removed.
        """
        return self.recv(size)

    def settimeout(self, value):
        """Set the read timeout for sockets, if value is 0 it will block"""
        self._timeout = value

    def available(self):
        """Returns how many bytes of data are available to be read (up to the MAX_PACKET length)"""
        if self.socknum != NO_SOCKET_AVAIL:
            return min(_the_interface.socket_available(self._socknum), MAX_PACKET)
        return 0

    def connected(self):
        """Whether or not we are connected to the socket"""
        if self.socknum == NO_SOCKET_AVAIL:
            return False
        if self.available():
            return True
        status = _the_interface.socket_status(self.socknum)
        result = status not in (
            adafruit_esp32spi.SOCKET_LISTEN,
            adafruit_esp32spi.SOCKET_CLOSED,
            adafruit_esp32spi.SOCKET_FIN_WAIT_1,
            adafruit_esp32spi.SOCKET_FIN_WAIT_2,
            adafruit_esp32spi.SOCKET_TIME_WAIT,
            adafruit_esp32spi.SOCKET_SYN_SENT,
            adafruit_esp32spi.SOCKET_SYN_RCVD,
            adafruit_esp32spi.SOCKET_CLOSE_WAIT,
        )
        if not result:
            self.close()
            self._socknum = NO_SOCKET_AVAIL
        return result

    @property
    def socknum(self):
        """The socket number"""
        return self._socknum

    def close(self):
        """Close the socket, after reading whatever remains"""
        _the_interface.socket_close(self._socknum)


# pylint: enable=unused-argument, redefined-builtin, invalid-name
