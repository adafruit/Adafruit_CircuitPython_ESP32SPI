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
        raise ValueError("Port must be an integer")
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
            raise ValueError("Only AF_INET family supported")
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
            raise ConnectionError("Failed to connect to host", host)
        self._buffer = b""

    def send(self, data):  # pylint: disable=no-self-use
        """Send some data to the socket."""
        if self._type is SOCK_DGRAM:
            conntype = _the_interface.UDP_MODE
        else:
            conntype = _the_interface.TCP_MODE
        _the_interface.socket_write(self._socknum, data, conn_mode=conntype)
        gc.collect()

    def recv(self, bufsize: int) -> bytes:
        """Reads some bytes from the connected remote address. Will only return
        an empty string after the configured timeout.

        :param int bufsize: maximum number of bytes to receive
        """
        buf = bytearray(bufsize)
        self.recv_into(buf, bufsize)
        return bytes(buf)

    def recv_into(self, buffer, nbytes: int = 0):
        """Read bytes from the connected remote address into a given buffer.

        :param bytearray buffer: the buffer to read into
        :param int nbytes: maximum number of bytes to receive; if 0,
            receive as many bytes as possible before filling the
            buffer or timing out
        """
        if not 0 <= nbytes <= len(buffer):
            raise ValueError("nbytes must be 0 to len(buffer)")

        last_read_time = time.monotonic()
        num_to_read = len(buffer) if nbytes == 0 else nbytes
        num_read = 0
        while num_to_read > 0:
            num_avail = self._available()
            if num_avail > 0:
                last_read_time = time.monotonic()
                bytes_read = _the_interface.socket_read(
                    self._socknum, min(num_to_read, num_avail)
                )
                buffer[num_read : num_read + len(bytes_read)] = bytes_read
                num_read += len(bytes_read)
                num_to_read -= num_read
            elif num_read > 0:
                # We got a message, but there are no more bytes to read, so we can stop.
                break
            # No bytes yet, or more bytes requested.
            if self._timeout > 0 and time.monotonic() - last_read_time > self._timeout:
                raise timeout("timed out")
        return num_read

    def settimeout(self, value):
        """Set the read timeout for sockets.
        If value is 0 socket reads will block until a message is available.
        """
        self._timeout = value

    def _available(self):
        """Returns how many bytes of data are available to be read (up to the MAX_PACKET length)"""
        if self._socknum != NO_SOCKET_AVAIL:
            return min(_the_interface.socket_available(self._socknum), MAX_PACKET)
        return 0

    def _connected(self):
        """Whether or not we are connected to the socket"""
        if self._socknum == NO_SOCKET_AVAIL:
            return False
        if self._available():
            return True
        status = _the_interface.socket_status(self._socknum)
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

    def close(self):
        """Close the socket, after reading whatever remains"""
        _the_interface.socket_close(self._socknum)


class timeout(TimeoutError):
    """TimeoutError class. An instance of this error will be raised by recv_into() if
    the timeout has elapsed and we haven't received any data yet."""

    def __init__(self, msg):
        super().__init__(msg)


# pylint: enable=unused-argument, redefined-builtin, invalid-name
