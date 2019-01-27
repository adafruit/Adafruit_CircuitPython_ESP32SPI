import struct
import time
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from micropython import const

class ESP_SPIcontrol:
    SET_NET_CMD           = const(0x10)
    SET_PASSPHRASE_CMD    = const(0x11)

    GET_CONN_STATUS_CMD   = const(0x20)
    GET_IPADDR_CMD        = const(0x21)
    GET_MACADDR_CMD       = const(0x22)
    GET_CURR_SSID_CMD     = const(0x23)
    GET_CURR_RSSI_CMD     = const(0x25)
    GET_CURR_ENCT_CMD     = const(0x26)

    SCAN_NETWORKS         = const(0x27)
    GET_SOCKET_CMD        = const(0x3F)
    GET_STATE_TCP_CMD     = const(0x29)
    DATA_SENT_TCP_CMD	  = const(0x2A)
    AVAIL_DATA_TCP_CMD	  = const(0x2B)
    GET_DATA_TCP_CMD	  = const(0x2C)
    START_CLIENT_TCP_CMD  = const(0x2D)
    STOP_CLIENT_TCP_CMD   = const(0x2E)
    GET_CLIENT_STATE_TCP_CMD = const(0x2F)
    DISCONNECT_CMD	      = const(0x30)
    GET_IDX_RSSI_CMD      = const(0x32)
    GET_IDX_ENCT_CMD      = const(0x33)
    REQ_HOST_BY_NAME_CMD  = const(0x34)
    GET_HOST_BY_NAME_CMD  = const(0x35)
    START_SCAN_NETWORKS   = const(0x36)
    GET_FW_VERSION_CMD    = const(0x37)
    PING_CMD			  = const(0x3E)

    SEND_DATA_TCP_CMD     = const(0x44)
    GET_DATABUF_TCP_CMD   = const(0x45)


    START_CMD             = const(0xE0)
    END_CMD               = const(0xEE)
    ERR_CMD               = const(0xEF)
    REPLY_FLAG            = const(1<<7)
    CMD_FLAG              = const(0)

    WL_NO_SHIELD          = const(0xFF)
    WL_NO_MODULE          = const(0xFF)
    WL_IDLE_STATUS        = const(0)
    WL_NO_SSID_AVAIL      = const(1)
    WL_SCAN_COMPLETED     = const(2)
    WL_CONNECTED          = const(3)

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

    TCP_MODE = const(0)

    def __init__(self, spi, cs_pin, ready_pin, reset_pin, gpio0_pin, *, debug=False):
        self._debug = debug
        self._buffer = bytearray(10)
        self._pbuf = bytearray(1)  # buffer for param read

        self._spi = spi
        self._cs = cs_pin
        self._ready = ready_pin
        self._reset = reset_pin
        self._gpio0 = gpio0_pin

        self._cs.direction = Direction.OUTPUT
        self._ready.direction = Direction.INPUT
        self._reset.direction = Direction.OUTPUT
        self._gpio0.direction = Direction.OUTPUT

        self._gpio0.value = True  # not bootload mode
        self._cs.value = True
        self._reset.value = False
        time.sleep(0.01)    # reset
        self._reset.value = True
        time.sleep(0.75)    # wait for it to boot up

        self._gpio0.direction = Direction.INPUT

    def spi_slave_select(self):
        while not self._spi.try_lock():
            pass
        self._spi.configure(baudrate=100000) # start slow
        self._cs.value = False # the actual select
        times = time.monotonic()
        while (time.monotonic() - times) < 0.1: # wait up to 100ms
            if self._ready.value:
                return
        raise RuntimeError("ESP32 timed out on SPI select")

    def slave_deselect(self):
        self._cs.value = True
        self._spi.unlock()

    def slave_ready(self):
        return self._ready.value == False

    def wait_for_slave_ready(self):
        if self._debug:
            print("Wait for slave ready", end='')
        while not self.slave_ready():
            if self._debug:
                print('.', end='')
            time.sleep(0.01)
        if self._debug:
            print()

    def wait_for_slave_select(self):
        self.wait_for_slave_ready()
        self.spi_slave_select()

    def send_command(self, cmd, params=None, *, param_len_16=False):
        if not params:
            params = []
        packet = []
        packet.append(START_CMD)
        packet.append(cmd & ~REPLY_FLAG)
        packet.append(len(params))

        # handle parameters here
        for i, param in enumerate(params):
            if self._debug:
                print("sending param #%d is %d bytes long" % (i, len(param)))
            if param_len_16:
                packet.append((len(param) >> 8) & 0xFF)
            packet.append(len(param) & 0xFF)
            packet += (param)

        packet.append(END_CMD)
        if self._debug:
            print("packet len:", len(packet))
        while len(packet) % 4 != 0:
            packet.append(0xFF)

        self.wait_for_slave_select()
        self._spi.write(bytearray(packet))
        if self._debug:
            print("Wrote: ", [hex(b) for b in packet])
        self.slave_deselect()

    def get_param(self):
        self._spi.readinto(self._pbuf)
        if self._debug:
            print("Read param", hex(self._pbuf[0]))
        return self._pbuf[0]

    def wait_spi_char(self, desired):
        times = time.monotonic()
        while (time.monotonic() - times) < 0.1:
            r = self.get_param()
            if r == ERR_CMD:
                raise RuntimeError("Error response to command")
            if r == desired:
                return True
        else:
            raise RuntimeError("Timed out waiting for SPI char")

    def check_data(self, desired):
        r = self.get_param()
        if r != desired:
            raise RuntimeError("Expected %02X but got %02X" % (desired, r))

    def wait_response_cmd(self, cmd, num_responses=None, *, param_len_16=False):
        self.wait_for_slave_ready()
        self.spi_slave_select()

        self.wait_spi_char(START_CMD)
        self.check_data(cmd | REPLY_FLAG)
        if num_responses is not None:
            self.check_data(num_responses)
        else:
            num_responses = self.get_param()
        responses = []
        for num in range(num_responses):
            response = []
            param_len = self.get_param()
            if param_len_16:
                param_len <<= 8
                param_len |= self.get_param()
            if self._debug:
                print("parameter #%d length is %d" % (num, param_len))
            for j in range(param_len):
                response.append(self.get_param())
            responses.append(bytes(response))
        self.check_data(END_CMD)

        self.slave_deselect()
        return responses

    def send_command_get_response(self, cmd, params=None, *,
                                  reply_params=1, sent_param_len_16=False,
                                  recv_param_len_16=False):
        self.send_command(cmd, params, param_len_16=sent_param_len_16)
        return self.wait_response_cmd(cmd, reply_params, param_len_16=recv_param_len_16)

    @property
    def status(self):
        if self._debug:
            print("Connection status")
        resp = self.send_command_get_response(GET_CONN_STATUS_CMD)
        if self._debug:
            print("Status:", resp[0][0])
        return resp[0][0]   # one byte response

    @property
    def firmware_version(self):
        if self._debug:
            print("Firmware version")
        resp = self.send_command_get_response(GET_FW_VERSION_CMD)
        return resp[0]

    @property
    def MAC_address(self):
        if self._debug:
            print("MAC address")
        resp = self.send_command_get_response(GET_MACADDR_CMD, [b'\xFF'])
        return resp[0]

    def start_scan_networks(self):
        if self._debug:
            print("Start scan")
        resp = self.send_command_get_response(START_SCAN_NETWORKS)
        if resp[0][0] != 1:
            raise RuntimeError("Failed to start AP scan")

    def get_scan_networks(self):
        self.send_command(SCAN_NETWORKS)
        names = self.wait_response_cmd(SCAN_NETWORKS)
        print("SSID names:", names)
        APs = []
        for i, name in enumerate(names):
            AP = {'ssid': name}
            rssi = self.send_command_get_response(GET_IDX_RSSI_CMD, [[i]])[0]
            AP['rssi'] = struct.unpack('<i', rssi)[0]
            encr = self.send_command_get_response(GET_IDX_ENCT_CMD, [[i]])[0]
            AP['encryption'] = encr[0]
            APs.append(AP)
        return APs

    def scan_networks(self):
        self.start_scan_networks()
        APs = None
        for _ in range(10):  # attempts
            time.sleep(2)
            APs = self.get_scan_networks()
            if len(APs):
                break
        return APs

    def wifi_set_network(self, ssid):
        resp = self.send_command_get_response(SET_NET_CMD, [ssid])
        if resp[0][0] != 1:
            raise RuntimeError("Failed to set network")

    def wifi_set_passphrase(self, ssid, passphrase):
        resp = self.send_command_get_response(SET_PASSPHRASE_CMD, [ssid, passphrase])
        if resp[0][0] != 1:
            raise RuntimeError("Failed to set passphrase")

    @property
    def ssid(self):
        resp = self.send_command_get_response(GET_CURR_SSID_CMD, [b'\xFF'])
        return resp[0]

    @property
    def rssi(self):
        resp = self.send_command_get_response(GET_CURR_RSSI_CMD, [b'\xFF'])
        return struct.unpack('<i', resp[0])[0]

    @property
    def network_data(self):
        resp = self.send_command_get_response(GET_IPADDR_CMD, [b'\xFF'], reply_params=3)
        return {'ip_addr': resp[0], 'netmask': resp[1], 'gateway': resp[2]}

    @property
    def ip_address(self):
        return self.network_data['ip_addr']

    def connect_AP(self, ssid, password):
        if self._debug:
            print("Connect to AP")
        if password:
            self.wifi_set_passphrase(ssid, password)
        else:
            self.wifi_set_network(ssid)
        for i in range(10): # retries
            stat = self.status
            if stat == WL_CONNECTED:
                return stat
            time.sleep(1)
        if stat in (WL_CONNECT_FAILED, WL_CONNECTION_LOST, WL_DISCONNECTED):
            raise RuntimeError("Failed to connect to ssid", ssid)
        if stat == WL_NO_SSID_AVAIL:
            raise RuntimeError("No such ssid", ssid)
        raise RuntimeError("Unknown error 0x%02X" % stat)

    def pretty_ip(self, ip):
        return "%d.%d.%d.%d" % (ip[0], ip[1], ip[2], ip[3])

    def unpretty_ip(self, ip):
        octets = [int(x) for x in ip.split('.')]
        return bytes(octets)

    def get_host_by_name(self, hostname):
        if self._debug:
            print("*** Get host by name")
        if isinstance(hostname, str):
            hostname = bytes(hostname, 'utf-8')
        resp = self.send_command_get_response(REQ_HOST_BY_NAME_CMD, [hostname])
        if resp[0][0] != 1:
            raise RuntimeError("Failed to request hostname")
        resp = self.send_command_get_response(GET_HOST_BY_NAME_CMD)
        return resp[0]

    def ping(self, dest, ttl=250):
        if isinstance(dest, str):          # convert to IP address
            dest = self.get_host_by_name(dest)
        # ttl must be between 0 and 255
        ttl = max(0, min(ttl, 255))
        resp = self.send_command_get_response(PING_CMD, [dest, [ttl]])
        return struct.unpack('<H', resp[0])[0]

    def get_socket(self):
        if self._debug:
            print("*** Get socket")
        resp = self.send_command_get_response(GET_SOCKET_CMD)
        resp = resp[0][0]
        if resp == 255:
            raise RuntimeError("No sockets available")
        return resp

    def socket_open(self, dest, ip, port, socket_num, conn_mode=TCP_MODE):
        if self._debug:
            print("*** Open socket")
        port_param = struct.pack('>H', port)
        resp = self.send_command_get_response(START_CLIENT_TCP_CMD,
                                              [ip, port_param,
                                               [socket_num], [conn_mode]])
        if resp[0][0] != 1:
            raise RuntimeError("Could not connect to remote server")

    def socket_status(self, socket_num):
        resp = self.send_command_get_response(GET_CLIENT_STATE_TCP_CMD, [[socket_num]])
        return resp[0][0]

    def socket_connected(self, socket_num):
        return self.socket_status(socket_num) == SOCKET_ESTABLISHED

    def socket_write(self, socket_num, buffer):
        resp = self.send_command_get_response(SEND_DATA_TCP_CMD,
                                              [[socket_num], buffer],
                                              sent_param_len_16=True)

        sent = resp[0][0]
        if sent != len(buffer):
            raise RuntimeError("Failed to send %d bytes (sent %d)" % (len(buffer), sent))
        return sent

    def socket_available(self, socket_num):
        resp = self.send_command_get_response(AVAIL_DATA_TCP_CMD, [[socket_num]])
        return struct.unpack('<H', resp[0])[0]

    def socket_read(self, socket_num, size):
        resp = self.send_command_get_response(GET_DATABUF_TCP_CMD, [[socket_num], [size]],
                                              sent_param_len_16=True, recv_param_len_16=True)
        return resp[0]

    def socket_connect(self, dest, port):
        if self._debug:
            print("*** Socket connect")
        if isinstance(dest, str):          # convert to IP address
            dest = self.get_host_by_name(dest)
        self.sock_num = self.get_socket()
        if self._debug:
            print("Allocated socket #%d" % self.sock_num)

        self.socket_open(dest, dest, port, self.sock_num)
        times = time.monotonic()
        while (time.monotonic() - times) < 3:  # wait 3 seconds
            if self.socket_connected(self.sock_num):
                return
            time.sleep(0.01)
        raise RuntimeError("Failed to establish connection")

    def socket_close(self, socket_num):
        resp = self.send_command_get_response(STOP_CLIENT_TCP_CMD, [[socket_num]])
        if resp[0][0] != 1:
            raise RuntimeError("Failed to close socket")
