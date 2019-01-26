import time
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from micropython import const

class ESP_SPIcontrol:
    GET_CONN_STATUS_CMD   = const(0x20)
    GET_FW_VERSION_CMD    = const(0x37)
    GET_MACADDR_CMD       = const(0x22)
    START_CMD             = const(0xE0)
    END_CMD               = const(0xEE)
    ERR_CMD               = const(0xEF)
    REPLY_FLAG            = const(1<<7)
    CMD_FLAG              = const(0)

    WL_NO_SHIELD          = const(0xFF)
    WL_NO_MODULE          = const(0xFF)
    WL_IDLE_STATUS        = const(0)

    def __init__(self, spi, cs_pin, ready_pin, reset_pin, gpio0_pin, *, debug=True):
        self.debug = debug
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

        print("Nina reset")
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
        print("wait for slave ready")
        while not self.slave_ready():
            print('.')

    def wait_for_slave_select(self):
        self.wait_for_slave_ready()
        self.spi_slave_select()


    def send_command(self, cmd, params=None):
        if not params:
            params = []
        packet = []
        packet.append(START_CMD)
        packet.append(cmd & ~REPLY_FLAG)
        packet.append(len(params))

        # handle parameters here
        for param in params:
            packet.append(len(param))
            packet += (param)

        packet.append(END_CMD)
        print("packet len:", len(packet))
        while len(packet) % 4 != 0:
            packet.append(0xFF)
        self._spi.write(bytearray(packet))
        print("Wrote: ", [hex(b) for b in packet])

    def get_param(self):
        self._spi.readinto(self._pbuf)
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

    def wait_response_cmd(self, cmd, num_responses):
        self.wait_spi_char(START_CMD)
        self.check_data(cmd | REPLY_FLAG)
        self.check_data(num_responses)
        responses = []
        for num in range(num_responses):
            response = []
            param_len = self.get_param()
            print("parameter #%d length is %d" % (num, param_len))
            for j in range(param_len):
                response.append(self.get_param())
            responses.append(response)
        self.check_data(END_CMD)
        return responses

    def get_connection_status(self):
        print("Connection status")
        self.wait_for_slave_select()
        self.send_command(GET_CONN_STATUS_CMD)
        self.slave_deselect()

        self.wait_for_slave_ready()
        self.spi_slave_select()
        resp = self.wait_response_cmd(GET_CONN_STATUS_CMD, 1)
        self.slave_deselect()
        print("Status:", resp[0][0])
        return resp[0][0]   # one byte response

    def get_firmware_version(self):
        print("Firmware version")
        self.wait_for_slave_select()
        self.send_command(GET_FW_VERSION_CMD)
        self.slave_deselect()

        self.wait_for_slave_ready()
        self.spi_slave_select()
        resp = self.wait_response_cmd(GET_FW_VERSION_CMD, 1)
        self.slave_deselect()
        return ''.join([chr(c) for c in resp[0]])

    def get_MAC(self):
        print("MAC address")
        self.wait_for_slave_select()
        self.send_command(GET_MACADDR_CMD, [[0xFF]])
        self.slave_deselect()

        self.wait_for_slave_ready()
        self.spi_slave_select()
        resp = self.wait_response_cmd(GET_MACADDR_CMD, 1)
        self.slave_deselect()
        return resp[0]
