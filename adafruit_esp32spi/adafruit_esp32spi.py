# SPDX-FileCopyrightText: Copyright (c) 2019 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

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

* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

import struct
import time
from micropython import const
from adafruit_bus_device.spi_device import SPIDevice
from digitalio import Direction

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI.git"

_SET_NET_CMD = const(0x10)
_SET_PASSPHRASE_CMD = const(0x11)
_SET_IP_CONFIG = const(0x14)
_SET_DNS_CONFIG = const(0x15)
_SET_HOSTNAME = const(0x16)
_SET_AP_NET_CMD = const(0x18)
_SET_AP_PASSPHRASE_CMD = const(0x19)
_SET_DEBUG_CMD = const(0x1A)

_GET_CONN_STATUS_CMD = const(0x20)
_GET_IPADDR_CMD = const(0x21)
_GET_MACADDR_CMD = const(0x22)
_GET_CURR_SSID_CMD = const(0x23)
_GET_CURR_BSSID_CMD = const(0x24)
_GET_CURR_RSSI_CMD = const(0x25)
_GET_CURR_ENCT_CMD = const(0x26)

_SCAN_NETWORKS = const(0x27)
_START_SERVER_TCP_CMD = const(0x28)
_GET_SOCKET_CMD = const(0x3F)
_GET_STATE_TCP_CMD = const(0x29)
_DATA_SENT_TCP_CMD = const(0x2A)
_AVAIL_DATA_TCP_CMD = const(0x2B)
_GET_DATA_TCP_CMD = const(0x2C)
_START_CLIENT_TCP_CMD = const(0x2D)
_STOP_CLIENT_TCP_CMD = const(0x2E)
_GET_CLIENT_STATE_TCP_CMD = const(0x2F)
_DISCONNECT_CMD = const(0x30)
_GET_IDX_RSSI_CMD = const(0x32)
_GET_IDX_ENCT_CMD = const(0x33)
_REQ_HOST_BY_NAME_CMD = const(0x34)
_GET_HOST_BY_NAME_CMD = const(0x35)
_START_SCAN_NETWORKS = const(0x36)
_GET_FW_VERSION_CMD = const(0x37)
_SEND_UDP_DATA_CMD = const(0x39)
_GET_REMOTE_DATA_CMD = const(0x3A)
_GET_TIME = const(0x3B)
_GET_IDX_BSSID_CMD = const(0x3C)
_GET_IDX_CHAN_CMD = const(0x3D)
_PING_CMD = const(0x3E)

_SEND_DATA_TCP_CMD = const(0x44)
_GET_DATABUF_TCP_CMD = const(0x45)
_INSERT_DATABUF_TCP_CMD = const(0x46)
_SET_ENT_IDENT_CMD = const(0x4A)
_SET_ENT_UNAME_CMD = const(0x4B)
_SET_ENT_PASSWD_CMD = const(0x4C)
_SET_ENT_ENABLE_CMD = const(0x4F)
_SET_CLI_CERT = const(0x40)
_SET_PK = const(0x41)

_SET_PIN_MODE_CMD = const(0x50)
_SET_DIGITAL_WRITE_CMD = const(0x51)
_SET_ANALOG_WRITE_CMD = const(0x52)
_SET_DIGITAL_READ_CMD = const(0x53)
_SET_ANALOG_READ_CMD = const(0x54)

_START_CMD = const(0xE0)
_END_CMD = const(0xEE)
_ERR_CMD = const(0xEF)
_REPLY_FLAG = const(1 << 7)
_CMD_FLAG = const(0)

SOCKET_CLOSED = const(0)
SOCKET_LISTEN = const(1)
SOCKET_SYN_SENT = const(2)
SOCKET_SYN_RCVD = const(3)
SOCKET_ESTABLISHED = const(4)
SOCKET_FIN_WAIT_1 = const(5)
SOCKET_FIN_WAIT_2 = const(6)
SOCKET_CLOSE_WAIT = const(7)
SOCKET_CLOSING = const(8)
SOCKET_LAST_ACK = const(9)
SOCKET_TIME_WAIT = const(10)

WL_NO_SHIELD = const(0xFF)
WL_NO_MODULE = const(0xFF)
WL_IDLE_STATUS = const(0)
WL_NO_SSID_AVAIL = const(1)
WL_SCAN_COMPLETED = const(2)
WL_CONNECTED = const(3)
WL_CONNECT_FAILED = const(4)
WL_CONNECTION_LOST = const(5)
WL_DISCONNECTED = const(6)
WL_AP_LISTENING = const(7)
WL_AP_CONNECTED = const(8)
WL_AP_FAILED = const(9)

ADC_ATTEN_DB_0 = const(0)
ADC_ATTEN_DB_2_5 = const(1)
ADC_ATTEN_DB_6 = const(2)
ADC_ATTEN_DB_11 = const(3)

# pylint: disable=too-many-lines


class Network:
    """A wifi network provided by a nearby access point."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        esp_spi_control=None,
        raw_ssid=None,
        raw_bssid=None,
        raw_rssi=None,
        raw_channel=None,
        raw_country=None,
        raw_authmode=None,
    ):
        self._esp_spi_control = esp_spi_control
        self._raw_ssid = raw_ssid
        self._raw_bssid = raw_bssid
        self._raw_rssi = raw_rssi
        self._raw_channel = raw_channel
        self._raw_country = raw_country
        self._raw_authmode = raw_authmode

    def _get_response(self, cmd):
        respose = self._esp_spi_control._send_command_get_response(  # pylint: disable=protected-access
            cmd, [b"\xFF"]
        )
        return respose[0]

    @property
    def ssid(self):
        """String id of the network"""
        if self._raw_ssid:
            response = self._raw_ssid
        else:
            response = self._get_response(_GET_CURR_SSID_CMD)
        return response.decode("utf-8")

    @property
    def bssid(self):
        """BSSID of the network (usually the AP’s MAC address)"""
        if self._raw_bssid:
            response = self._raw_bssid
        else:
            response = self._get_response(_GET_CURR_BSSID_CMD)
        return bytes(response)

    @property
    def rssi(self):
        """Signal strength of the network"""
        if self._raw_bssid:
            response = self._raw_rssi
        else:
            response = self._get_response(_GET_CURR_RSSI_CMD)
        return struct.unpack("<i", response)[0]

    @property
    def channel(self):
        """Channel number the network is operating on"""
        if self._raw_channel:
            return self._raw_channel[0]
        return None

    @property
    def country(self):
        """String id of the country code"""
        return self._raw_country

    @property
    def authmode(self):
        """String id of the authmode

        derived from Nina code:
        https://github.com/adafruit/nina-fw/blob/master/arduino/libraries/WiFi/src/WiFi.cpp#L385
        """
        if self._raw_authmode:
            response = self._raw_authmode[0]
        else:
            response = self._get_response(_GET_CURR_ENCT_CMD)[0]

        if response == 7:
            return "OPEN"
        if response == 5:
            return "WEP"
        if response == 2:
            return "PSK"
        if response == 4:
            return "WPA2"
        return "UNKNOWN"


class ESP_SPIcontrol:  # pylint: disable=too-many-public-methods, too-many-instance-attributes
    """A class that will talk to an ESP32 module programmed with special firmware
    that lets it act as a fast an efficient WiFi co-processor"""

    TCP_MODE = const(0)
    UDP_MODE = const(1)
    TLS_MODE = const(2)

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        spi,
        cs_dio,
        ready_dio,
        reset_dio,
        gpio0_dio=None,
        *,
        debug=False,
        debug_show_secrets=False,
    ):
        self._debug = debug
        self._debug_show_secrets = debug_show_secrets
        self.set_psk = False
        self.set_crt = False
        self._buffer = bytearray(10)
        self._pbuf = bytearray(1)  # buffer for param read
        self._sendbuf = bytearray(256)  # buffer for command sending
        self._socknum_ll = [[0]]  # pre-made list of list of socket #

        self._spi_device = SPIDevice(spi, cs_dio, baudrate=8000000)
        self._cs = cs_dio
        self._ready = ready_dio
        self._reset = reset_dio
        self._gpio0 = gpio0_dio
        self._cs.direction = Direction.OUTPUT
        self._ready.direction = Direction.INPUT
        self._reset.direction = Direction.OUTPUT
        # Only one TLS socket at a time is supported so track when we already have one.
        self._tls_socket = None
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
        time.sleep(0.01)  # reset
        self._reset.value = True
        time.sleep(0.75)  # wait for it to boot up
        if self._gpio0:
            self._gpio0.direction = Direction.INPUT

    def _wait_for_ready(self):
        """Wait until the ready pin goes low"""
        if self._debug >= 3:
            print("Wait for ESP32 ready", end="")
        times = time.monotonic()
        while (time.monotonic() - times) < 10:  # wait up to 10 seconds
            if not self._ready.value:  # we're ready!
                break
            if self._debug >= 3:
                print(".", end="")
                time.sleep(0.05)
        else:
            raise TimeoutError("ESP32 not responding")
        if self._debug >= 3:
            print()

    # pylint: disable=too-many-branches
    def _send_command(self, cmd, params=None, *, param_len_16=False):
        """Send over a command with a list of parameters"""
        if not params:
            params = ()

        packet_len = 4  # header + end byte
        for i, param in enumerate(params):
            packet_len += len(param)  # parameter
            packet_len += 1  # size byte
            if param_len_16:
                packet_len += 1  # 2 of em here!
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
                self._sendbuf[ptr + j] = par
            ptr += len(param)
        self._sendbuf[ptr] = _END_CMD

        self._wait_for_ready()
        with self._spi_device as spi:
            times = time.monotonic()
            while (time.monotonic() - times) < 1:  # wait up to 1000ms
                if self._ready.value:  # ok ready to send!
                    break
            else:
                raise TimeoutError("ESP32 timed out on SPI select")
            spi.write(
                self._sendbuf, start=0, end=packet_len
            )  # pylint: disable=no-member
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
        """Read a byte with a retry loop, and if we get it, check that its what we expect"""
        for _ in range(10):
            r = self._read_byte(spi)
            if r == _ERR_CMD:
                raise BrokenPipeError("Error response to command")
            if r == desired:
                return True
            time.sleep(0.01)
        raise TimeoutError("Timed out waiting for SPI char")

    def _check_data(self, spi, desired):
        """Read a byte and verify its the value we want"""
        r = self._read_byte(spi)
        if r != desired:
            raise BrokenPipeError("Expected %02X but got %02X" % (desired, r))

    def _wait_response_cmd(self, cmd, num_responses=None, *, param_len_16=False):
        """Wait for ready, then parse the response"""
        self._wait_for_ready()

        responses = []
        with self._spi_device as spi:
            times = time.monotonic()
            while (time.monotonic() - times) < 1:  # wait up to 1000ms
                if self._ready.value:  # ok ready to send!
                    break
            else:
                raise TimeoutError("ESP32 timed out on SPI select")

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

    def _send_command_get_response(  # pylint: disable=too-many-arguments
        self,
        cmd,
        params=None,
        *,
        reply_params=1,
        sent_param_len_16=False,
        recv_param_len_16=False,
    ):
        """Send a high level SPI command, wait and return the response"""
        self._send_command(cmd, params, param_len_16=sent_param_len_16)
        return self._wait_response_cmd(
            cmd, reply_params, param_len_16=recv_param_len_16
        )

    @property
    def status(self):
        """The status of the ESP32 WiFi core. Can be WL_NO_SHIELD or WL_NO_MODULE
        (not found), WL_IDLE_STATUS, WL_NO_SSID_AVAIL, WL_SCAN_COMPLETED,
        WL_CONNECTED, WL_CONNECT_FAILED, WL_CONNECTION_LOST, WL_DISCONNECTED,
        WL_AP_LISTENING, WL_AP_CONNECTED, WL_AP_FAILED"""
        resp = self._send_command_get_response(_GET_CONN_STATUS_CMD)
        if self._debug:
            print("Connection status:", resp[0][0])
        return resp[0][0]  # one byte response

    @property
    def firmware_version(self):
        """A string of the firmware version on the ESP32"""
        if self._debug:
            print("Firmware version")
        resp = self._send_command_get_response(_GET_FW_VERSION_CMD)
        return resp[0].decode("utf-8").replace("\x00", "")

    @property
    def MAC_address(self):  # pylint: disable=invalid-name
        """A bytearray containing the MAC address of the ESP32"""
        if self._debug:
            print("MAC address")
        resp = self._send_command_get_response(_GET_MACADDR_CMD, [b"\xFF"])
        return resp[0]

    @property
    def MAC_address_actual(self):  # pylint: disable=invalid-name
        """A bytearray containing the actual MAC address of the ESP32"""
        return bytearray(reversed(self.MAC_address))

    @property
    def mac_address(self):
        """A bytes containing the actual MAC address of the ESP32"""
        return bytes(self.MAC_address_actual)

    def start_scan_networks(self):
        """Begin a scan of visible access points. Follow up with a call
        to 'get_scan_networks' for response"""
        if self._debug:
            print("Start scan")
        resp = self._send_command_get_response(_START_SCAN_NETWORKS)
        if resp[0][0] != 1:
            raise OSError("Failed to start AP scan")

    def get_scan_networks(self):
        """The results of the latest SSID scan. Returns a list of dictionaries with
        'ssid', 'rssi', 'encryption', bssid, and channel entries, one for each AP found
        """
        self._send_command(_SCAN_NETWORKS)
        names = self._wait_response_cmd(_SCAN_NETWORKS)
        # print("SSID names:", names)
        APs = []  # pylint: disable=invalid-name
        for i, name in enumerate(names):
            bssid = self._send_command_get_response(_GET_IDX_BSSID_CMD, ((i,),))[0]
            rssi = self._send_command_get_response(_GET_IDX_RSSI_CMD, ((i,),))[0]
            channel = self._send_command_get_response(_GET_IDX_CHAN_CMD, ((i,),))[0]
            authmode = self._send_command_get_response(_GET_IDX_ENCT_CMD, ((i,),))[0]
            APs.append(
                Network(
                    raw_ssid=name,
                    raw_bssid=bssid,
                    raw_rssi=rssi,
                    raw_channel=channel,
                    raw_authmode=authmode,
                )
            )
        return APs

    def scan_networks(self):
        """Scan for visible access points, returns a list of access point details.
        Returns a list of dictionaries with 'ssid', 'rssi' and 'encryption' entries,
        one for each AP found"""
        self.start_scan_networks()
        for _ in range(10):  # attempts
            time.sleep(2)
            APs = self.get_scan_networks()  # pylint: disable=invalid-name
            if APs:
                return APs
        return None

    def set_ip_config(self, ip_address, gateway, mask="255.255.255.0"):
        """Tells the ESP32 to set ip, gateway and network mask b"\xFF"

        :param str ip_address: IP address (as a string).
        :param str gateway: Gateway (as a string).
        :param str mask: Mask, defaults to 255.255.255.0 (as a string).
        """
        resp = self._send_command_get_response(
            _SET_IP_CONFIG,
            params=[
                b"\x00",
                self.unpretty_ip(ip_address),
                self.unpretty_ip(gateway),
                self.unpretty_ip(mask),
            ],
            sent_param_len_16=False,
        )
        return resp

    def set_dns_config(self, dns1, dns2):
        """Tells the ESP32 to set DNS

        :param str dns1: DNS server 1 IP as a string.
        :param str dns2: DNS server 2 IP as a string.
        """
        resp = self._send_command_get_response(
            _SET_DNS_CONFIG, [b"\x00", self.unpretty_ip(dns1), self.unpretty_ip(dns2)]
        )
        if resp[0][0] != 1:
            raise OSError("Failed to set dns with esp32")

    def set_hostname(self, hostname):
        """Tells the ESP32 to set hostname for DHCP.

        :param str hostname: The new host name.
        """
        resp = self._send_command_get_response(_SET_HOSTNAME, [hostname.encode()])
        if resp[0][0] != 1:
            raise OSError("Failed to set hostname with esp32")

    def wifi_set_network(self, ssid):
        """Tells the ESP32 to set the access point to the given ssid"""
        resp = self._send_command_get_response(_SET_NET_CMD, [ssid])
        if resp[0][0] != 1:
            raise OSError("Failed to set network")

    def wifi_set_passphrase(self, ssid, passphrase):
        """Sets the desired access point ssid and passphrase"""
        resp = self._send_command_get_response(_SET_PASSPHRASE_CMD, [ssid, passphrase])
        if resp[0][0] != 1:
            raise OSError("Failed to set passphrase")

    def wifi_set_entidentity(self, ident):
        """Sets the WPA2 Enterprise anonymous identity"""
        resp = self._send_command_get_response(_SET_ENT_IDENT_CMD, [ident])
        if resp[0][0] != 1:
            raise OSError("Failed to set enterprise anonymous identity")

    def wifi_set_entusername(self, username):
        """Sets the desired WPA2 Enterprise username"""
        resp = self._send_command_get_response(_SET_ENT_UNAME_CMD, [username])
        if resp[0][0] != 1:
            raise OSError("Failed to set enterprise username")

    def wifi_set_entpassword(self, password):
        """Sets the desired WPA2 Enterprise password"""
        resp = self._send_command_get_response(_SET_ENT_PASSWD_CMD, [password])
        if resp[0][0] != 1:
            raise OSError("Failed to set enterprise password")

    def wifi_set_entenable(self):
        """Enables WPA2 Enterprise mode"""
        resp = self._send_command_get_response(_SET_ENT_ENABLE_CMD)
        if resp[0][0] != 1:
            raise OSError("Failed to enable enterprise mode")

    def _wifi_set_ap_network(self, ssid, channel):
        """Creates an Access point with SSID and Channel"""
        resp = self._send_command_get_response(_SET_AP_NET_CMD, [ssid, channel])
        if resp[0][0] != 1:
            raise OSError("Failed to setup AP network")

    def _wifi_set_ap_passphrase(self, ssid, passphrase, channel):
        """Creates an Access point with SSID, passphrase, and Channel"""
        resp = self._send_command_get_response(
            _SET_AP_PASSPHRASE_CMD, [ssid, passphrase, channel]
        )
        if resp[0][0] != 1:
            raise OSError("Failed to setup AP password")

    @property
    def ap_info(self):
        """Network object containing BSSID, SSID, authmode, channel, country and RSSI when
        connected to an access point. None otherwise."""
        if self.is_connected:
            return Network(esp_spi_control=self)
        return None

    @property
    def network_data(self):
        """A dictionary containing current connection details such as the 'ip_addr',
        'netmask' and 'gateway'"""
        resp = self._send_command_get_response(
            _GET_IPADDR_CMD, [b"\xFF"], reply_params=3
        )
        return {"ip_addr": resp[0], "netmask": resp[1], "gateway": resp[2]}

    @property
    def ip_address(self):
        """Our local IP address"""
        return self.network_data["ip_addr"]

    @property
    def connected(self):
        """Whether the ESP32 is connected to an access point"""
        try:
            return self.status == WL_CONNECTED
        except OSError:
            self.reset()
            return False

    @property
    def is_connected(self):
        """Whether the ESP32 is connected to an access point"""
        return self.connected

    @property
    def ap_listening(self):
        """Returns if the ESP32 is in access point mode and is listening for connections"""
        try:
            return self.status == WL_AP_LISTENING
        except OSError:
            self.reset()
            return False

    def disconnect(self):
        """Disconnect from the access point"""
        resp = self._send_command_get_response(_DISCONNECT_CMD)
        if resp[0][0] != 1:
            raise OSError("Failed to disconnect")

    def connect(self, ssid, password=None, timeout=10):
        """Connect to an access point with given name and password.

        **Deprecated functionality:** If the first argument (``ssid``) is a ``dict``,
        assume it is a dictionary with entries for keys ``"ssid"`` and, optionally, ``"password"``.
        This mimics the previous signature for ``connect()``.
        This upward compatbility will be removed in a future release.
        """
        if isinstance(ssid, dict):  # secrets
            ssid, password = ssid["ssid"], ssid.get("password")
        self.connect_AP(ssid, password, timeout_s=timeout)

    def connect_AP(self, ssid, password, timeout_s=10):  # pylint: disable=invalid-name
        """Connect to an access point with given name and password.
        Will wait until specified timeout seconds and return on success
        or raise an exception on failure.

        :param ssid: the SSID to connect to
        :param passphrase: the password of the access point
        :param timeout_s: number of seconds until we time out and fail to create AP
        """
        if self._debug:
            print(
                f"Connect to AP: {ssid=}, password=\
                    {repr(password if self._debug_show_secrets else '*' * len(password))}"
            )
        if isinstance(ssid, str):
            ssid = bytes(ssid, "utf-8")
        if password:
            if isinstance(password, str):
                password = bytes(password, "utf-8")
            self.wifi_set_passphrase(ssid, password)
        else:
            self.wifi_set_network(ssid)
        times = time.monotonic()
        while (time.monotonic() - times) < timeout_s:  # wait up until timeout
            stat = self.status
            if stat == WL_CONNECTED:
                return stat
            time.sleep(0.05)
        if stat in (WL_CONNECT_FAILED, WL_CONNECTION_LOST, WL_DISCONNECTED):
            raise ConnectionError("Failed to connect to ssid", ssid)
        if stat == WL_NO_SSID_AVAIL:
            raise ConnectionError("No such ssid", ssid)
        raise OSError("Unknown error 0x%02X" % stat)

    def create_AP(
        self, ssid, password, channel=1, timeout=10
    ):  # pylint: disable=invalid-name
        """Create an access point with the given name, password, and channel.
        Will wait until specified timeout seconds and return on success
        or raise an exception on failure.

        :param str ssid: the SSID of the created Access Point. Must be less than 32 chars.
        :param str password: the password of the created Access Point. Must be 8-63 chars.
        :param int channel: channel of created Access Point (1 - 14).
        :param int timeout: number of seconds until we time out and fail to create AP
        """
        if len(ssid) > 32:
            raise ValueError("ssid must be no more than 32 characters")
        if password and (len(password) < 8 or len(password) > 64):
            raise ValueError("password must be 8 - 63 characters")
        if channel < 1 or channel > 14:
            raise ValueError("channel must be between 1 and 14")

        if isinstance(channel, int):
            channel = bytes(channel)
        if isinstance(ssid, str):
            ssid = bytes(ssid, "utf-8")
        if password:
            if isinstance(password, str):
                password = bytes(password, "utf-8")
            self._wifi_set_ap_passphrase(ssid, password, channel)
        else:
            self._wifi_set_ap_network(ssid, channel)

        times = time.monotonic()
        while (time.monotonic() - times) < timeout:  # wait up to timeout
            stat = self.status
            if stat == WL_AP_LISTENING:
                return stat
            time.sleep(0.05)
        if stat == WL_AP_FAILED:
            raise ConnectionError("Failed to create AP", ssid)
        raise OSError("Unknown error 0x%02x" % stat)

    @property
    def ipv4_address(self):
        """IP address of the station when connected to an access point."""
        return self.pretty_ip(self.ip_address)

    def pretty_ip(self, ip):  # pylint: disable=no-self-use, invalid-name
        """Converts a bytearray IP address to a dotted-quad string for printing"""
        return "%d.%d.%d.%d" % (ip[0], ip[1], ip[2], ip[3])

    def unpretty_ip(self, ip):  # pylint: disable=no-self-use, invalid-name
        """Converts a dotted-quad string to a bytearray IP address"""
        octets = [int(x) for x in ip.split(".")]
        return bytes(octets)

    def get_host_by_name(self, hostname):
        """Convert a hostname to a packed 4-byte IP address. Returns
        a 4 bytearray"""
        if self._debug:
            print("*** Get host by name")
        if isinstance(hostname, str):
            hostname = bytes(hostname, "utf-8")
        resp = self._send_command_get_response(_REQ_HOST_BY_NAME_CMD, (hostname,))
        if resp[0][0] != 1:
            raise ConnectionError("Failed to request hostname")
        resp = self._send_command_get_response(_GET_HOST_BY_NAME_CMD)
        return resp[0]

    def ping(self, dest, ttl=250):
        """Ping a destination IP address or hostname, with a max time-to-live
        (ttl). Returns a millisecond timing value"""
        if isinstance(dest, str):  # convert to IP address
            dest = self.get_host_by_name(dest)
        # ttl must be between 0 and 255
        ttl = max(0, min(ttl, 255))
        resp = self._send_command_get_response(_PING_CMD, (dest, (ttl,)))
        return struct.unpack("<H", resp[0])[0]

    def get_socket(self):
        """Request a socket from the ESP32, will allocate and return a number that
        can then be passed to the other socket commands"""
        if self._debug:
            print("*** Get socket")
        resp = self._send_command_get_response(_GET_SOCKET_CMD)
        resp = resp[0][0]
        if resp == 255:
            raise OSError(23)  # ENFILE - File table overflow
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
            print("*** Open socket to", dest, port, conn_mode)
        if conn_mode == ESP_SPIcontrol.TLS_MODE and self._tls_socket is not None:
            raise OSError(23, "Only one open SSL connection allowed")
        port_param = struct.pack(">H", port)
        if isinstance(dest, str):  # use the 5 arg version
            dest = bytes(dest, "utf-8")
            resp = self._send_command_get_response(
                _START_CLIENT_TCP_CMD,
                (
                    dest,
                    b"\x00\x00\x00\x00",
                    port_param,
                    self._socknum_ll[0],
                    (conn_mode,),
                ),
            )
        else:  # ip address, use 4 arg vesion
            resp = self._send_command_get_response(
                _START_CLIENT_TCP_CMD,
                (dest, port_param, self._socknum_ll[0], (conn_mode,)),
            )
        if resp[0][0] != 1:
            raise ConnectionError("Could not connect to remote server")
        if conn_mode == ESP_SPIcontrol.TLS_MODE:
            self._tls_socket = socket_num

    def socket_status(self, socket_num):
        """Get the socket connection status, can be SOCKET_CLOSED, SOCKET_LISTEN,
        SOCKET_SYN_SENT, SOCKET_SYN_RCVD, SOCKET_ESTABLISHED, SOCKET_FIN_WAIT_1,
        SOCKET_FIN_WAIT_2, SOCKET_CLOSE_WAIT, SOCKET_CLOSING, SOCKET_LAST_ACK, or
        SOCKET_TIME_WAIT"""
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(
            _GET_CLIENT_STATE_TCP_CMD, self._socknum_ll
        )
        return resp[0][0]

    def socket_connected(self, socket_num):
        """Test if a socket is connected to the destination, returns boolean true/false"""
        return self.socket_status(socket_num) == SOCKET_ESTABLISHED

    def socket_write(self, socket_num, buffer, conn_mode=TCP_MODE):
        """Write the bytearray buffer to a socket"""
        if self._debug:
            print("Writing:", buffer)
        self._socknum_ll[0][0] = socket_num
        sent = 0
        total_chunks = (len(buffer) // 64) + 1
        send_command = _SEND_DATA_TCP_CMD
        if conn_mode == self.UDP_MODE:  # UDP requires a different command to write
            send_command = _INSERT_DATABUF_TCP_CMD
        for chunk in range(total_chunks):
            resp = self._send_command_get_response(
                send_command,
                (
                    self._socknum_ll[0],
                    memoryview(buffer)[(chunk * 64) : ((chunk + 1) * 64)],
                ),
                sent_param_len_16=True,
            )
            sent += resp[0][0]

        if conn_mode == self.UDP_MODE:
            # UDP verifies chunks on write, not bytes
            if sent != total_chunks:
                raise ConnectionError(
                    "Failed to write %d chunks (sent %d)" % (total_chunks, sent)
                )
            # UDP needs to finalize with this command, does the actual sending
            resp = self._send_command_get_response(_SEND_UDP_DATA_CMD, self._socknum_ll)
            if resp[0][0] != 1:
                raise ConnectionError("Failed to send UDP data")
            return

        if sent != len(buffer):
            self.socket_close(socket_num)
            raise ConnectionError(
                "Failed to send %d bytes (sent %d)" % (len(buffer), sent)
            )

        resp = self._send_command_get_response(_DATA_SENT_TCP_CMD, self._socknum_ll)
        if resp[0][0] != 1:
            raise ConnectionError("Failed to verify data sent")

    def socket_available(self, socket_num):
        """Determine how many bytes are waiting to be read on the socket"""
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(_AVAIL_DATA_TCP_CMD, self._socknum_ll)
        reply = struct.unpack("<H", resp[0])[0]
        if self._debug:
            print("ESPSocket: %d bytes available" % reply)
        return reply

    def socket_read(self, socket_num, size):
        """Read up to 'size' bytes from the socket number. Returns a bytes"""
        if self._debug:
            print(
                "Reading %d bytes from ESP socket with status %d"
                % (size, self.socket_status(socket_num))
            )
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(
            _GET_DATABUF_TCP_CMD,
            (self._socknum_ll[0], (size & 0xFF, (size >> 8) & 0xFF)),
            sent_param_len_16=True,
            recv_param_len_16=True,
        )
        return bytes(resp[0])

    def socket_connect(self, socket_num, dest, port, conn_mode=TCP_MODE):
        """Open and verify we connected a socket to a destination IP address or hostname
        using the ESP32's internal reference number. By default we use
        'conn_mode' TCP_MODE but can also use UDP_MODE or TLS_MODE (dest must
        be hostname for TLS_MODE!)"""
        if self._debug:
            print("*** Socket connect mode", conn_mode)

        self.socket_open(socket_num, dest, port, conn_mode=conn_mode)
        if conn_mode == self.UDP_MODE:
            # UDP doesn't actually establish a connection
            # but the socket for writing is created via start_server
            self.start_server(port, socket_num, conn_mode)
            return True

        times = time.monotonic()
        while (time.monotonic() - times) < 3:  # wait 3 seconds
            if self.socket_connected(socket_num):
                return True
            time.sleep(0.01)
        raise TimeoutError("Failed to establish connection")

    def socket_close(self, socket_num):
        """Close a socket using the ESP32's internal reference number"""
        if self._debug:
            print("*** Closing socket #%d" % socket_num)
        self._socknum_ll[0][0] = socket_num
        try:
            self._send_command_get_response(_STOP_CLIENT_TCP_CMD, self._socknum_ll)
        except OSError:
            pass
        if socket_num == self._tls_socket:
            self._tls_socket = None

    def start_server(
        self, port, socket_num, conn_mode=TCP_MODE, ip=None
    ):  # pylint: disable=invalid-name
        """Opens a server on the specified port, using the ESP32's internal reference number"""
        if self._debug:
            print("*** starting server")
        self._socknum_ll[0][0] = socket_num
        params = [struct.pack(">H", port), self._socknum_ll[0], (conn_mode,)]
        if ip:
            params.insert(0, ip)
        resp = self._send_command_get_response(_START_SERVER_TCP_CMD, params)

        if resp[0][0] != 1:
            raise OSError("Could not start server")

    def server_state(self, socket_num):
        """Get the state of the ESP32's internal reference server socket number"""
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(_GET_STATE_TCP_CMD, self._socknum_ll)
        return resp[0][0]

    def get_remote_data(self, socket_num):
        """Get the IP address and port of the remote host"""
        self._socknum_ll[0][0] = socket_num
        resp = self._send_command_get_response(
            _GET_REMOTE_DATA_CMD, self._socknum_ll, reply_params=2
        )
        return {"ip_addr": resp[0], "port": struct.unpack("<H", resp[1])[0]}

    def set_esp_debug(self, enabled):
        """Enable/disable debug mode on the ESP32. Debug messages will be
        written to the ESP32's UART."""
        resp = self._send_command_get_response(_SET_DEBUG_CMD, ((bool(enabled),),))
        if resp[0][0] != 1:
            raise OSError("Failed to set debug mode")

    def set_pin_mode(self, pin, mode):
        """Set the io mode for a GPIO pin.

        :param int pin: ESP32 GPIO pin to set.
        :param value: direction for pin, digitalio.Direction or integer (0=input, 1=output).
        """
        if mode == Direction.OUTPUT:
            pin_mode = 1
        elif mode == Direction.INPUT:
            pin_mode = 0
        else:
            pin_mode = mode
        resp = self._send_command_get_response(_SET_PIN_MODE_CMD, ((pin,), (pin_mode,)))
        if resp[0][0] != 1:
            raise OSError("Failed to set pin mode")

    def set_digital_write(self, pin, value):
        """Set the digital output value of pin.

        :param int pin: ESP32 GPIO pin to write to.
        :param bool value: Value for the pin.
        """
        resp = self._send_command_get_response(
            _SET_DIGITAL_WRITE_CMD, ((pin,), (value,))
        )
        if resp[0][0] != 1:
            raise OSError("Failed to write to pin")

    def set_analog_write(self, pin, analog_value):
        """Set the analog output value of pin, using PWM.

        :param int pin: ESP32 GPIO pin to write to.
        :param float value: 0=off 1.0=full on
        """
        value = int(255 * analog_value)
        resp = self._send_command_get_response(
            _SET_ANALOG_WRITE_CMD, ((pin,), (value,))
        )
        if resp[0][0] != 1:
            raise OSError("Failed to write to pin")

    def set_digital_read(self, pin):
        """Get the digital input value of pin. Returns the boolean value of the pin.

        :param int pin: ESP32 GPIO pin to read from.
        """
        # Verify nina-fw => 1.5.0
        fw_semver_maj = self.firmware_version[2]
        assert int(fw_semver_maj) >= 5, "Please update nina-fw to 1.5.0 or above."

        resp = self._send_command_get_response(_SET_DIGITAL_READ_CMD, ((pin,),))[0]
        if resp[0] == 0:
            return False
        if resp[0] == 1:
            return True
        raise OSError(
            "_SET_DIGITAL_READ response error: response is not boolean", resp[0]
        )

    def set_analog_read(self, pin, atten=ADC_ATTEN_DB_11):
        """Get the analog input value of pin. Returns an int between 0 and 65536.

        :param int pin: ESP32 GPIO pin to read from.
        :param int atten: attenuation constant
        """
        # Verify nina-fw => 1.5.0
        fw_semver_maj = self.firmware_version[2]
        assert int(fw_semver_maj) >= 5, "Please update nina-fw to 1.5.0 or above."

        resp = self._send_command_get_response(_SET_ANALOG_READ_CMD, ((pin,), (atten,)))
        resp_analog = struct.unpack("<i", resp[0])
        if resp_analog[0] < 0:
            raise ValueError(
                "_SET_ANALOG_READ parameter error: invalid pin", resp_analog[0]
            )
        if self._debug:
            print(resp, resp_analog, resp_analog[0], 16 * resp_analog[0])
        return 16 * resp_analog[0]

    def get_time(self):
        """The current unix timestamp"""
        if self.status == WL_CONNECTED:
            resp = self._send_command_get_response(_GET_TIME)
            resp_time = struct.unpack("<i", resp[0])
            if resp_time == (0,):
                raise OSError("_GET_TIME returned 0")
            return resp_time
        if self.status in (WL_AP_LISTENING, WL_AP_CONNECTED):
            raise OSError(
                "Cannot obtain NTP while in AP mode, must be connected to internet"
            )
        raise OSError("Must be connected to WiFi before obtaining NTP.")

    def set_certificate(self, client_certificate):
        """Sets client certificate. Must be called
        BEFORE a network connection is established.

        :param str client_certificate: User-provided .PEM certificate up to 1300 bytes.
        """
        if self._debug:
            print("** Setting client certificate")
        if self.status == WL_CONNECTED:
            raise ValueError(
                "set_certificate must be called BEFORE a connection is established."
            )
        if isinstance(client_certificate, str):
            client_certificate = bytes(client_certificate, "utf-8")
        if "-----BEGIN CERTIFICATE" not in client_certificate:
            raise TypeError(".PEM must start with -----BEGIN CERTIFICATE")
        assert len(client_certificate) < 1300, ".PEM must be less than 1300 bytes."
        resp = self._send_command_get_response(_SET_CLI_CERT, (client_certificate,))
        if resp[0][0] != 1:
            raise OSError("Failed to set client certificate")
        self.set_crt = True
        return resp[0]

    def set_private_key(self, private_key):
        """Sets private key. Must be called
        BEFORE a network connection is established.

        :param str private_key: User-provided .PEM file up to 1700 bytes.
        """
        if self._debug:
            print("** Setting client's private key.")
        if self.status == WL_CONNECTED:
            raise ValueError(
                "set_private_key must be called BEFORE a connection is established."
            )
        if isinstance(private_key, str):
            private_key = bytes(private_key, "utf-8")
        if "-----BEGIN RSA" not in private_key:
            raise TypeError(".PEM must start with -----BEGIN RSA")
        assert len(private_key) < 1700, ".PEM must be less than 1700 bytes."
        resp = self._send_command_get_response(_SET_PK, (private_key,))
        if resp[0][0] != 1:
            raise OSError("Failed to set private key.")
        self.set_psk = True
        return resp[0]
