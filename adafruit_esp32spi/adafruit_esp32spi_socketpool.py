# SPDX-FileCopyrightText: Copyright (c) 2019 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_esp32spi_socketpool`
================================================================================

A socket compatible interface thru the ESP SPI command set

* Author(s): ladyada
"""

from __future__ import annotations

try:
    from typing import TYPE_CHECKING, Optional, Tuple

    if TYPE_CHECKING:
        from esp32spi.adafruit_esp32spi import ESP_SPIcontrol  # noqa: UP007
except ImportError:
    pass


import errno
import gc
import time

from micropython import const

from adafruit_esp32spi import adafruit_esp32spi as esp32spi

_global_socketpool = {}


class SocketPool:
    """ESP32SPI SocketPool library"""

    # socketpool constants
    SOCK_STREAM = const(1)
    SOCK_DGRAM = const(2)
    AF_INET = const(2)
    SOL_SOCKET = const(0xFFF)
    SO_REUSEADDR = const(0x0004)

    # implementation specific constants
    NO_SOCKET_AVAIL = const(255)
    MAX_PACKET = const(4000)

    def __new__(cls, iface: ESP_SPIcontrol):
        # We want to make sure to return the same pool for the same interface
        if iface not in _global_socketpool:
            _global_socketpool[iface] = super().__new__(cls)
        return _global_socketpool[iface]

    def __init__(self, iface: ESP_SPIcontrol):
        self._interface = iface

    def getaddrinfo(self, host, port, family=0, socktype=0, proto=0, flags=0):
        """Given a hostname and a port name, return a 'socket.getaddrinfo'
        compatible list of tuples. Honestly, we ignore anything but host & port"""
        if not isinstance(port, int):
            raise ValueError("Port must be an integer")
        ipaddr = self._interface.get_host_by_name(host)
        return [(SocketPool.AF_INET, socktype, proto, "", (ipaddr, port))]

    def socket(
        self,
        family=AF_INET,
        type=SOCK_STREAM,
        proto=0,
        fileno=None,
    ):
        """Create a new socket and return it"""
        return Socket(self, family, type, proto, fileno)


class Socket:
    """A simplified implementation of the Python 'socket' class, for connecting
    through an interface to a remote device. Has properties specific to the
    implementation.

    :param SocketPool socket_pool: The underlying socket pool.
    :param Optional[int] socknum: Allows wrapping a Socket instance around a socket
                              number returned by the nina firmware. Used internally.
    """

    def __init__(
        self,
        socket_pool: SocketPool,
        family: int = SocketPool.AF_INET,
        type: int = SocketPool.SOCK_STREAM,
        proto: int = 0,
        fileno: Optional[int] = None,  # noqa: UP007
        socknum: Optional[int] = None,  # noqa: UP007
    ):
        if family != SocketPool.AF_INET:
            raise ValueError("Only AF_INET family supported")
        self._socket_pool = socket_pool
        self._interface = self._socket_pool._interface
        self._type = type
        self._buffer = b""
        self._socknum = socknum if socknum is not None else self._interface.get_socket()
        self._bound = ()
        self.settimeout(None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
        while self._interface.socket_status(self._socknum) != esp32spi.SOCKET_CLOSED:
            pass

    def connect(self, address, conntype=None):
        """Connect the socket to the 'address' (which can be 32bit packed IP or
        a hostname string). 'conntype' is an extra that may indicate SSL or not,
        depending on the underlying interface"""
        host, port = address
        if conntype is None:
            conntype = (
                self._interface.UDP_MODE
                if self._type == SocketPool.SOCK_DGRAM
                else self._interface.TCP_MODE
            )
        if not self._interface.socket_connect(self._socknum, host, port, conn_mode=conntype):
            raise ConnectionError("Failed to connect to host", host)
        self._buffer = b""

    def send(self, data):
        """Send some data to the socket."""
        if self._type == SocketPool.SOCK_DGRAM:
            conntype = self._interface.UDP_MODE
        else:
            conntype = self._interface.TCP_MODE
        sent = self._interface.socket_write(self._socknum, data, conn_mode=conntype)
        gc.collect()
        return sent

    def sendto(self, data, address):
        """Connect and send some data to the socket."""
        self.connect(address)
        return self.send(data)

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

        last_read_time = time.monotonic_ns()
        num_to_read = len(buffer) if nbytes == 0 else nbytes
        num_read = 0
        while num_to_read > 0:
            # we might have read socket data into the self._buffer with:
            # adafruit_wsgi.esp32spi_wsgiserver: socket_readline
            if len(self._buffer) > 0:
                bytes_to_read = min(num_to_read, len(self._buffer))
                buffer[num_read : num_read + bytes_to_read] = self._buffer[:bytes_to_read]
                num_read += bytes_to_read
                num_to_read -= bytes_to_read
                self._buffer = self._buffer[bytes_to_read:]
                # explicitly recheck num_to_read to avoid extra checks
                continue

            num_avail = self._available()
            if num_avail > 0:
                last_read_time = time.monotonic_ns()
                bytes_read = self._interface.socket_read(self._socknum, min(num_to_read, num_avail))
                buffer[num_read : num_read + len(bytes_read)] = bytes_read
                num_read += len(bytes_read)
                num_to_read -= len(bytes_read)
            elif num_read > 0:
                # We got a message, but there are no more bytes to read, so we can stop.
                break
            # No bytes yet, or more bytes requested.

            if self._timeout == 0:  # if in non-blocking mode, stop now.
                break

            # Time out if there's a positive timeout set.
            delta = (time.monotonic_ns() - last_read_time) // 1_000_000
            if self._timeout > 0 and delta > self._timeout:
                raise OSError(errno.ETIMEDOUT)
        return num_read

    def settimeout(self, value):
        """Set the read timeout for sockets in seconds.
        ``0`` means non-blocking. ``None`` means block indefinitely.
        """
        if value is None:
            self._timeout = -1
        else:
            if value < 0:
                raise ValueError("Timeout cannot be a negative number")
            # internally in milliseconds as an int
            self._timeout = int(value * 1000)

    def _available(self):
        """Returns how many bytes of data are available to be read (up to the MAX_PACKET length)"""
        if self._socknum != SocketPool.NO_SOCKET_AVAIL:
            return min(self._interface.socket_available(self._socknum), SocketPool.MAX_PACKET)
        return 0

    def _connected(self):
        """Whether or not we are connected to the socket"""
        if self._socknum == SocketPool.NO_SOCKET_AVAIL:
            return False
        if self._available():
            return True
        status = self._interface.socket_status(self._socknum)
        result = status not in {
            esp32spi.SOCKET_LISTEN,
            esp32spi.SOCKET_CLOSED,
            esp32spi.SOCKET_FIN_WAIT_1,
            esp32spi.SOCKET_FIN_WAIT_2,
            esp32spi.SOCKET_TIME_WAIT,
            esp32spi.SOCKET_SYN_SENT,
            esp32spi.SOCKET_SYN_RCVD,
            esp32spi.SOCKET_CLOSE_WAIT,
        }
        if not result:
            self.close()
            self._socknum = SocketPool.NO_SOCKET_AVAIL
        return result

    def close(self):
        """Close the socket, after reading whatever remains"""
        self._interface.socket_close(self._socknum)

    def accept(self):
        """Accept a connection on a listening socket of type SOCK_STREAM,
        creating a new socket of type SOCK_STREAM. Returns a tuple of
        (new_socket, remote_address)
        """
        client_sock_num = self._interface.socket_available(self._socknum)
        if client_sock_num != SocketPool.NO_SOCKET_AVAIL:
            sock = Socket(self._socket_pool, socknum=client_sock_num)
            # get remote information (addr and port)
            remote = self._interface.get_remote_data(client_sock_num)
            ip_address = "{}.{}.{}.{}".format(*remote["ip_addr"])
            port = remote["port"]
            client_address = (ip_address, port)
            return sock, client_address
        raise OSError(errno.ECONNRESET)

    def bind(self, address: tuple[str, int]):
        """Bind a socket to an address"""
        self._bound = address

    def listen(self, backlog: int):  # pylint: disable=unused-argument
        """Set socket to listen for incoming connections.
        :param int backlog: length of backlog queue for waiting connections (ignored)
        """
        if not self._bound:
            self._bound = (self._interface.ip_address, 80)
        port = self._bound[1]
        self._interface.start_server(port, self._socknum)

    def setblocking(self, flag: bool):
        """Set the blocking behaviour of this socket.
        :param bool flag: False means non-blocking, True means block indefinitely.
        """
        if flag:
            self.settimeout(None)
        else:
            self.settimeout(0)

    def setsockopt(self, *opts, **kwopts):
        """Dummy call for compatibility."""
