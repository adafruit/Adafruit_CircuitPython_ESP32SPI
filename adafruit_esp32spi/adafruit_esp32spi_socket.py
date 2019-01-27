"""A 'socket' compatible interface thru the ESP SPI command set"""
from micropython import const

_the_interface = None   # pylint: disable=invalid-name
def set_interface(iface):
    """Helper to set the global internet interface"""
    global _the_interface   # pylint: disable=global-statement, invalid-name
    _the_interface = iface

SOCK_STREAM = const(1)
AF_INET = const(2)

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

    def readline(self):
        """Attempt to return as many bytes as we can up to but not including '\r\n'"""
        while b'\r\n' not in self._buffer:
            # there's no line already in there, read some more
            avail = _the_interface.socket_available(self._socknum)
            if avail:
                self._buffer += _the_interface.socket_read(self._socknum, avail)
        firstline, self._buffer = self._buffer.split(b'\r\n', 1)
        return firstline

    def read(self, size=0):
        """Read up to 'size' bytes from the socket, this may be buffered internally!
        If 'size' isnt specified, return everything in the buffer."""
        avail = _the_interface.socket_available(self._socknum)
        if avail:
            self._buffer += _the_interface.socket_read(self._socknum, avail)
        if size == 0:   # read as much as we can
            ret = self._buffer
            self._buffer = b''
            return ret
        while len(self._buffer) < size:
            avail = _the_interface.socket_available(self._socknum)
            if avail:
                self._buffer += _the_interface.socket_read(self._socknum, avail)
        ret = self._buffer[:size]
        self._buffer = self._buffer[size:]
        return ret

    def close(self):
        """Close the socket, after reading whatever remains"""
        _the_interface.socket_close(self._socknum)
# pylint: enable=unused-argument, redefined-builtin, invalid-name
