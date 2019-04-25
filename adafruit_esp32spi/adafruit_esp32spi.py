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
`adafruit_esp32spi`
================================================================================

CircuitPython driver library for using ESP32 as WiFi  co-processor using SPI


* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

import struct
import time
from micropython import const
from digitalio import Direction
from adafruit_bus_device.spi_device import SPIDevice

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI.git"

# pylint: disable=bad-whitespace
_SET_NET_CMD           = const(0x10)
_SET_PASSPHRASE_CMD    = const(0x11)
_SET_DEBUG_CMD         = const(0x1A)

_GET_CONN_STATUS_CMD   = const(0x20)
_GET_IPADDR_CMD        = const(0x21)
_GET_MACADDR_CMD       = const(0x22)
_GET_CURR_SSID_CMD     = const(0x23)
_GET_CURR_RSSI_CMD     = const(0x25)
_GET_CURR_ENCT_CMD     = const(0x26)

_SCAN_NETWORKS         = const(0x27)
_GET_SOCKET_CMD        = const(0x3F)
_GET_STATE_TCP_CMD     = const(0x29)
_DATA_SENT_TCP_CMD	   = const(0x2A)
_AVAIL_DATA_TCP_CMD	   = const(0x2B)
_GET_DATA_TCP_CMD	   = const(0x2C)
_START_CLIENT_TCP_CMD  = const(0x2D)
_STOP_CLIENT_TCP_CMD   = const(0x2E)
_GET_CLIENT_STATE_TCP_CMD = const(0x2F)
_DISCONNECT_CMD	       = const(0x30)
_GET_IDX_RSSI_CMD      = const(0x32)
_GET_IDX_ENCT_CMD      = const(0x33)
_REQ_HOST_BY_NAME_CMD  = const(0x34)
_GET_HOST_BY_NAME_CMD  = const(0x35)
_START_SCAN_NETWORKS   = const(0x36)
_GET_FW_VERSION_CMD    = const(0x37)
_PING_CMD			   = const(0x3E)

_SEND_DATA_TCP_CMD     = const(0x44)
_GET_DATABUF_TCP_CMD   = const(0x45)
_SET_ENT_IDENT_CMD     = const(0x4A)
_SET_ENT_UNAME_CMD     = const(0x4B)
_SET_ENT_PASSWD_CMD    = const(0x4C)
_SET_ENT_ENABLE_CMD    = const(0x4F)

_SET_PIN_MODE_CMD      = const(0x50)
_SET_DIGITAL_WRITE_CMD = const(0x51)
_SET_ANALOG_WRITE_CMD  = const(0x52)

_START_CMD             = const(0xE0)
_END_CMD               = const(0xEE)
_ERR_CMD               = const(0xEF)
_REPLY_FLAG            = const(1<<7)
_CMD_FLAG              = const(0)

SOCKET_CLOSED      = const(0)
SOCKET_LISTEN      = const(1)
SOCKET_SYN_SENT    = const(2)
SOCKET_SYN_RCVD    = const(3)
SOCKET_ESTABLISHED = const(4)
SOCKET_FIN_WAIT_1  = const(5)
SOCKET_FIN_WAIT_2  = const(6)
SOCKET_CLOSE_WAIT  = const(7)
SOCKET_CLOSING     = const(8)
SOCKET_LAST_ACK    = const(9)
SOCKET_TIME_WAIT   = const(10)

WL_NO_SHIELD          = const(0xFF)
WL_NO_MODULE          = const(0xFF)
WL_IDLE_STATUS        = const(0)
WL_NO_SSID_AVAIL      = const(1)
WL_SCAN_COMPLETED     = const(2)
WL_CONNECTED          = const(3)
WL_CONNECT_FAILED     = const(4)
WL_CONNECTION_LOST    = const(5)
WL_DISCONNECTED       = const(6)
WL_AP_LISTENING       = const(7)
WL_AP_CONNECTED       = const(8)
WL_AP_FAILED          = const(9)
# pylint: enable=bad-whitespace

class ESP_SPIcontrol:  # pylint: disable=too-many-public-methods
    """A class that will talk to an ESP32 module programmed with special firmware
    that lets it act as a fast an efficient WiFi co-processor"""
    TCP_MODE = const(0)
    UDP_MODE = const(1)
    TLS_MODE = const(2)

    # pylint: disable=too-many-arguments
    def __init__(self, spi, cs_pin, ready_pin, reset_pin, gpio0_pin=None, *, debug=False):
        self._debug = debug
        self._buffer = bytearray(10)
        self._pbuf = bytearray(1)  # buffer for param read
        self._sendbuf = bytearray(256)  # buffer for command sending
        self._socknum_ll = [[0]]      # pre-made list of list of socket #

        self._spi_device = SPIDevice(spi, cs_pin, baudrate=8000000)
        self._cs = cs_pin
        self._ready = ready_pin
        self._reset = reset_pin
        self._gpio0 = gpio0_pin
        self._cs.direction = Direction.OUTPUT
        self._ready.direction = Direction.INPUT
        self._reset.direction = Direction.OUTPUT
        if self._gpio0:
            self._gpio0.direction = Direction.INPUT
        self.reset()
    # pylint: enable=too-many-arguments

    def reset(self):
        """Hard reset the ESP32 using the reset pin"""
        if self._debug:
            print("Reset ESP32")
        if self._gpio0:
            self._gpio0.direction = Direction.OUTPUT
            self._gpio0.value = True  # not bootload mode
        self._cs.value = True
        self._reset.value = False
        time.sleep(0.01)    # reset
        self._reset.value = True
        time.sleep(0.75)    # wait for it to boot up
        if self._gpio0:
            self._gpio0.direction = Direction.INPUT

    def _wait_for_ready(self):
        """Wait until the ready pin goes low"""
        if self._debug >= 3:
            print("Wait for ESP32 ready", end='')
        times = time.monotonic()
        while (time.monotonic() - times) < 10:  # wait up to 10 seconds
            if not self._ready.value: # we're ready!
                break
            if self._debug >= 3:
                print('.', end='')
                time.sleep(0.05)
        else:
            raise RuntimeError("ESP32 not responding")
        if self._debug >= 3:
            print()

    # pylint: disable=too-many-branches
    def _send_command(self, cmd, params=None, *, param_len_16=False):
        """Send over a command with a list of parameters"""
        if not params:
            params = ()

        packet_len = 4 # header + end byte
        for i, param in enumerate(params):
            packet_len += len(param)   # parameter
            packet_len += 1            # size byte
            if param_len_16:
                packet_len += 1        # 2 of em here!
        while packet_len % 4 != 0:
            packet_len += 1
        # we may need more space
        if packet_len > len(self._sendbuf):
            self._sendbuf = bytearray(packet_len)

        self._sendbuf[0] = _START_CMD
        self._sendbuf[1] = cmd & ~_REPLY_FLAG
        self._sendbuf[2] = len(params)

        # handle parameters here
        ptr = 3
        for i, param in enumerate(params):
            if self._debug >= 2:
                print("\tSending param #%d is %d bytes long" % (i, len(param)))
            if param_len_16:
                self._sendbuf[ptr] = (len(param) >> 8) & 0xFF
                ptr += 1
            self._sendbuf[ptr] = len(param) & 0xFF
            ptr += 1
            for j, par in enumerate(param):
                self._sendbuf[ptr+j] = par
            ptr += len(param)
        self._sendbuf[ptr] = _END_CMD

        self._wait_for_ready()
        with self._spi_device as spi:
            times = time.monotonic()
            while (time.monotonic() - times) < 1: # wait up to 1000ms
                if self._ready.value:  # ok ready to send!
                    break
            else:
                raise RuntimeError("ESP32 timed out on SPI select")
            spi.write(self._sendbuf, start=0, end=packet_len)  # pylint: disable=no-member
            if self._debug >= 3:
                print("Wrote: ", [hex(b) for b in self._sendbuf[0:packet_len]])
    # pylint: disable=too-many-branches

    def _read_byte(self, spi):
        """Read one byte from SPI"""
        spi.readinto(self._pbuf)
        if self._debug >= 3:
            print("\t\tRead:", hex(self._pbuf[0]))
        return self._pbuf[0]

    def _read_bytes(self, spi, buffer, start=0, end=None):
        """Read many bytes from SPI"""
        if not end:
            end = len(buffer)
        spi.readinto(buffer, start=start, end=end)
        if self._debug >= 3:
            print("\t\tRead:", [hex(i) for i in buffer])

    def _wait_spi_char(self, spi, desired):
        """Read a byte with a time-out, and if we get it, check that its what we expect"""
        times = time.monotonic()
        while (time.monotonic() - times) < 0.1:
            r = self._read_byte(spi)
            if r == _ERR_CMD:
                raise RuntimeError("Error response to command")
            if r == desired:
                return True
        raise RuntimeError("Timed out waiting for SPI char")

    def _check_data(self, spi, desired):
        """Read a byte and verify its the value we want"""
        r = self._read_byte(spi)
        if r != desired:
            raise RuntimeError("Expected %02X but got %02X" % (desired, r))

    def _wait_response_cmd(self, cmd, num_responses=None, *, param_len_16=False):
        """Wait for ready, then parse the response"""
        self._wait_for_ready()

        responses = []
        with self._spi_device as spi:
            times = time.monotonic()
            while (time.monotonic() - times) < 1: # wait up to 1000ms
                if self._ready.value:  # ok ready to send!
                    break
            else:
                raise RuntimeError("ESP32 timed out on SPI select")

            self._wait_spi_char(spi, _START_CMD)
            self._check_data(spi, cmd | _REPLY_FLAG)
            if num_responses is not None:
                self._check_data(spi, num_responses)
            else:
                num_responses = self._read_byte(spi)
            for num in range(num_responses):
                param_len = self._read_byte(spi)
                if param_len_16:
                    param_len <<= 8
                    param_len |= self._read_byte(spi)
                if self._debug >= 2:
                    print("\tParameter #%d length is %d" % (num, param_len))
                response = bytearray(param_len)
                self._read_bytes(spi, response)
                responses.append(response)
            self._check_data(spi, _END_CMD)

        if self._debug >= 2:
            print("Read %d: " % len(responses[0]), responses)
        return responses

    def _send_command_get_response(self, cmd, params=None, *,
                                   reply_params=1, sent_param_len_16=False,
                                   recv_param_len_16=False):
        """Send a high level SPI command, wait and return the response"""
        self._send_command(cmd, params, param_len_16=sent_param_len_16)
        return self._wait_response_cmd(cmd, reply_params, param_len_16=recv_param_len_16)

    @property
    def status(self):
        """The status of the ESP32 WiFi core. Can be WL_NO_SHIELD or WL_NO_MODULE
        (not found), WL_IDLE_STATUS, WL_NO_SSID_AVAIL, WL_SCAN_COMPLETED,
        WL_CONNECTED, WL_CONNECT_FAILED, WL_CONNECTION_LOST, WL_DISCONNECTED,
        WL_AP_LISTENING, WL_AP_CONNECTED, WL_AP_FAILED"""
        if self._debug:
            print("Connection status")
        resp = self._send_command_get_response(_GET_CONN_STATUS_CMD)
        if self._debug:
            print("Conn status:", resp[0][0])
        return resp[0][0]   # one byte response

    @property
    def firmware_version(self):
        """A string of the firmware version on the ESP32"""
        if self._debug:
            print("Firmware version")
        resp = self._send_command_get_response(_GET_FW_VERSION_CMD)
        return resp[0]

    @property
    def MAC_address(self):        # pylint: disable=invalid-name
        """A bytearray containing the MAC address of the ESP32"""
        if self._debug:
            print("MAC address")
        resp = self._send_command_get_response(_GET_MACADDR_CMD, [b'\xFF'])
        return resp[0]

    def start_scan_networks(self):
        """Begin a scan of visible access points. Follow up with a call
        to 'get_scan_networks' for response"""
        if self._debug:
            print("Start scan")
        resp = self._send_command_get_response(_START_SCAN_NETWORKS)
        if resp[0][0] != 1:
            raise RuntimeError("Failed to start AP scan")

    def get_scan_networks(self):
        """The results of the latest SSID scan. Returns a list of dictionaries with
        'ssid', 'rssi' and 'encryption' entries, one for each AP found"""
        self._send_command(_SCAN_NETWORKS)
        names = self._wait_response_cmd(_SCAN_NETWORKS)
        #print("SSID names:", names)
        APs = []                         # pylint: disable=invalid-name
        for i, name in enumerate(names):
            a_p = {'ssid': name}
            rssi = self._send_command_get_response(_GET_IDX_RSSI_CMD, ((i,),))[0]
            a_p['rssi'] = struct.unpack('<i', rssi)[0]
            encr = self._send_command_get_response(_GET_IDX_ENCT_CMD, ((i,),))[0]
            a_p['encryption'] = encr[0]
            APs.append(a_p)
        return APs

    def scan_networks(self):
        """Scan for visible access points, returns a list of access point details.
         Returns a list of dictionaries with 'ssid', 'rssi' and 'encryption' entries,
         one for each AP found"""
        self.start_scan_networks()
        for _ in range(10):  # attempts
            time.sleep(2)
            APs = self.get_scan_networks() # pylint: disable=invalid-name
            if APs:
                return APs
        return None

    def wifi_set_network(self, ssid):
        """Tells the ESP32 to set the access point to the given ssid"""
        resp = self._send_command_get_response(_SET_NET_CMD, [ssid])
        if resp[0][0] != 1:
            raise RuntimeError("Failed to set network")

    def wifi_set_passphrase(self, ssid, passphrase):
        """Sets the desired access point ssid and passphrase"""
        resp = self._send_command_get_response(_SET_PASSPHRASE_CMD, [ssid, passphrase])
        if resp[0][0] != 1:
            raise RuntimeError("Failed to set passphrase")

    def wifi_set_entidentity(self, ident):
        """Sets the WPA2 Enterprise anonymous identity"""
        resp = self._send_command_get_response(_SET_ENT_IDENT_CMD, [ident])
        if resp[0][0] != 1:
            raise RuntimeError("Failed to set enterprise anonymous identity")

    def wifi_set_entusername(self, username):
        """Sets the desired WPA2 Enterprise username"""
        resp = self._send_command_get_response(_SET_ENT_UNAME_CMD, [username])
        if resp[0][0] != 1:
            raise RuntimeError("Failed to set enterprise username")

    def wifi_set_entpassword(self, password):
        """Sets the desired WPA2 Enterprise password"""
        resp = self._send_command_get_response(_SET_ENT_PASSWD_CMD, [password])
        if resp[0][0] != 1:
            raise RuntimeError("Failed to set enterprise password")

    def wifi_set_entenable(self):
        """Enables WPA2 Enterprise mode"""
        resp = self._send_command_get_response(_SET_ENT_ENABLE_CMD)
        if resp[0][0] != 1:
            raise RuntimeError("Failed to enable enterprise mode")

    @property
    def ssid(self):
        """The name of the access point we're connected to"""
        resp = self._send_command_get_response(_GET_CURR_SSID_CMD, [b'\xFF'])
        return resp[0]

    @property
    def rssi(self):
        """The receiving signal strength indicator for the access point we're
        connected to"""
        resp = self._send_command_get_response(_GET_CURR_RSSI_CMD, [b'\xFF'])
        return struct.unpack('<i', resp[0])[0]

    @property
    def network_data(self):
        """A dictionary containing current connection details such as the 'ip_addr',
        'netmask' and 'gateway'"""
        resp = self._send_command_get_response(_GET_IPADDR_CMD, [b'\xFF'], reply_params=3)
        return {'ip_addr': resp[0], 'netmask': resp[1], 'gateway': resp[2]}

    @property
    def ip_address(self):
        """Our local IP address"""
        return self.network_data['ip_addr']

    @property
    def is_connected(self):
        """Whether the ESP32 is connected to an access point"""
        try:
            return self.status == WL_CONNECTED
        except RuntimeError:
            self.reset()
            return False

    def connect(self, secrets):
        """Connect to an access point using a secrets dictionary
        that contains a 'ssid' and 'password' entry"""
        self.connect_AP(secrets['ssid'], secrets['password'])

    def connect_AP(self, ssid, password): # pylint: disable=invalid-name
        """Connect to an access point with given name and password.
        Will retry up to 10 times and return on success or raise
        an exception on failure"""
        if self._debug:
            print("Connect to AP", ssid, password)
        if isinstance(ssid, str):
            ssid = bytes(ssid, 'utf-8')
        if password:
            if isinstance(password, str):
                password = bytes(password, 'utf-8')
            self.wifi_set_passphrase(ssid, password)
        else:
            self.wifi_set_network(ssid)
        for _ in range(10): # retries
            stat = self.status
            if stat == WL_CONNECTED:
                return stat
            time.sleep(1)
        if stat in (WL_CONNECT_FAILED, WL_CONNECTION_LOST, WL_DISCONNECTED):
            raise RuntimeError("Failed to connect to ssid", ssid)
        if stat == WL_NO_SSID_AVAIL:
            raise RuntimeError("No such ssid", ssid)
        raise RuntimeError("Unknown error 0x%02X" % stat)

    def pretty_ip(self, ip): # pylint: disable=no-self-use, invalid-name
        """Converts a bytearray IP address to a dotted-quad string for printing"""
        return "%d.%d.%d.%d" % (ip[0], ip[1], ip[2], ip[3])

    def unpretty_ip(self, ip): # pylint: disable=no-self-use, invalid-name
        """Converts a dotted-quad string to a bytearray IP address"""
        octets = [int(x) for x in ip.split('.')]
        return bytes(octets)

    def get_host_by_name(self, hostname):
        """Convert a hostname to a packed 4-byte IP address. Returns
        a 4 bytearray"""
        if self._debug:
            print("*** Get host by name")
        if isinstance(hostname, str):
            hostname = bytes(hostname, 'utf-8')
        resp = self._send_command_get_response(_REQ_HOST_BY_NAME_CMD, (hostname,))
        if resp[0][0] != 1:
            raise RuntimeError("Failed to request hostname")
        resp = self._send_command_get_response(_GET_HOST_BY_NAME_CMD)
        return resp[0]

    def ping(self, dest, ttl=250):
        """Ping a destination IP address or hostname, with a max time-to-live
        (ttl). Returns a millisecond timing value"""
        if isinstance(dest, str):          # convert to IP address
            dest = self.get_host_by_name(dest)
        # ttl must be between 0 and 255
        ttl = max(0, min(ttl, 255))
        resp = self._send_command_get_response(_PING_CMD, (dest, (ttl,)))
        return struct.unpack('<H', resp[0])[0]

    def get_socket(self):
        """Request a socket from the ESP32, will allocate and return a number that
        can then be passed to the other socket commands"""
        if self._debug:
            print("*** Get socket")
        resp = self._send_command_get_response(_GET_SOCKET_CMD)
        resp = resp[0][0]
        if resp == 255:
            raise RuntimeError("No sockets available")
        if self._debug:
            print("Allocated socket #%d" % resp)
        return resp

    def socket_open(self, socket_num, dest, port, conn_mode=TCP_MODE):
        """Open a socket to a destination IP address or hostname
        using the ESP32's internal reference number. By default we use
        'conn_mode' TCP_MODE but can also use UDP_MODE or TLS_MODE
        (dest must be hostname for TLS_MODE!)"""
        self._socknum_ll[0][0] = socket_num
        if self._debug:
            print("*** Open socket")
        port_param = struct.pack('>H', port)
        if isinstance(dest, str):          # use the 5 arg version
            dest = bytes(dest, 'utf-8')
            resp = self._send_command_get_response(_START_CLIENT_TCP_CMD,
                                                   (dest, b'\x00\x00\x00\x00',
                                                    port_param,
                                                    self._socknum_ll[0],
                                                    (conn_mode,)))
        else:                              # ip address, use 4 arg vesion
            resp = self._send_command_get_response(_START_CLIENT_TCP_CMD,
                                                   (dest, port_param,
                                                    self._socknum_ll[0],
                                                    (conn_mode,)))
        if resp[0][0] != 1:
            raise RuntimeError("Could not connect to remote server")

    def socket_status(self, socket_num):
        """Get the socket connection status, can be SOCKET_CLOSED, SOCKET_LISTEN,
        SOCKET_SYN_SENT, SOCKET_SYN_RCVD, SOCKET_ESTABLISHED, SOCKET_FIN_WAIT_1,
        SOCKET_FIN_WAIT_2, SOCKET_CLOSE_WAIT, SOCKET_CLOSING, SOCKET_LAST_ACK, or
        SOCKET_TIME_WAIT"""
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(_GET_CLIENT_STATE_TCP_CMD, self._socknum_ll)
        return resp[0][0]

    def socket_connected(self, socket_num):
        """Test if a socket is connected to the destination, returns boolean true/false"""
        return self.socket_status(socket_num) == SOCKET_ESTABLISHED

    def socket_write(self, socket_num, buffer):
        """Write the bytearray buffer to a socket"""
        if self._debug:
            print("Writing:", buffer)
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(_SEND_DATA_TCP_CMD,
                                               (self._socknum_ll[0], buffer),
                                               sent_param_len_16=True)

        sent = resp[0][0]
        if sent != len(buffer):
            raise RuntimeError("Failed to send %d bytes (sent %d)" % (len(buffer), sent))

        resp = self._send_command_get_response(_DATA_SENT_TCP_CMD, self._socknum_ll)
        if resp[0][0] != 1:
            raise RuntimeError("Failed to verify data sent")

    def socket_available(self, socket_num):
        """Determine how many bytes are waiting to be read on the socket"""
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(_AVAIL_DATA_TCP_CMD, self._socknum_ll)
        reply = struct.unpack('<H', resp[0])[0]
        if self._debug:
            print("ESPSocket: %d bytes available" % reply)
        return reply

    def socket_read(self, socket_num, size):
        """Read up to 'size' bytes from the socket number. Returns a bytearray"""
        if self._debug:
            print("Reading %d bytes from ESP socket with status %d" %
                  (size, self.socket_status(socket_num)))
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(_GET_DATABUF_TCP_CMD,
                                               (self._socknum_ll[0],
                                                (size & 0xFF, (size >> 8) & 0xFF)),
                                               sent_param_len_16=True,
                                               recv_param_len_16=True)
        return bytes(resp[0])

    def socket_connect(self, socket_num, dest, port, conn_mode=TCP_MODE):
        """Open and verify we connected a socket to a destination IP address or hostname
        using the ESP32's internal reference number. By default we use
        'conn_mode' TCP_MODE but can also use UDP_MODE or TLS_MODE (dest must
        be hostname for TLS_MODE!)"""
        if self._debug:
            print("*** Socket connect mode", conn_mode)

        self.socket_open(socket_num, dest, port, conn_mode=conn_mode)
        times = time.monotonic()
        while (time.monotonic() - times) < 3:  # wait 3 seconds
            if self.socket_connected(socket_num):
                return True
            time.sleep(0.01)
        raise RuntimeError("Failed to establish connection")

    def socket_close(self, socket_num):
        """Close a socket using the ESP32's internal reference number"""
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(_STOP_CLIENT_TCP_CMD, self._socknum_ll)
        if resp[0][0] != 1:
            raise RuntimeError("Failed to close socket")

    def set_esp_debug(self, enabled):
        """Enable/disable debug mode on the ESP32. Debug messages will be
        written to the ESP32's UART."""
        resp = self._send_command_get_response(_SET_DEBUG_CMD, ((bool(enabled),),))
        if resp[0][0] != 1:
            raise RuntimeError("Failed to set debug mode")

    def set_pin_mode(self, pin, mode):
        """
        Set the io mode for a GPIO pin.

        :param int pin: ESP32 GPIO pin to set.
        :param value: direction for pin, digitalio.Direction or integer (0=input, 1=output).
        """
        if mode == Direction.OUTPUT:
            pin_mode = 1
        elif mode == Direction.INPUT:
            pin_mode = 0
        else:
            pin_mode = mode
        resp = self._send_command_get_response(_SET_PIN_MODE_CMD,
                                               ((pin,), (pin_mode,)))
        if resp[0][0] != 1:
            raise RuntimeError("Failed to set pin mode")

    def set_digital_write(self, pin, value):
        """
        Set the digital output value of pin.

        :param int pin: ESP32 GPIO pin to write to.
        :param bool value: Value for the pin.
        """
        resp = self._send_command_get_response(_SET_DIGITAL_WRITE_CMD,
                                               ((pin,), (value,)))
        if resp[0][0] != 1:
            raise RuntimeError("Failed to write to pin")

    def set_analog_write(self, pin, analog_value):
        """
        Set the analog output value of pin, using PWM.

        :param int pin: ESP32 GPIO pin to write to.
        :param float value: 0=off 1.0=full on
        """
        value = int(255 * analog_value)
        resp = self._send_command_get_response(_SET_ANALOG_WRITE_CMD,
                                               ((pin,), (value,)))
        if resp[0][0] != 1:
            raise RuntimeError("Failed to write to pin")
