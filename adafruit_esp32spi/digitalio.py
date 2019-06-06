# The MIT License (MIT)
#
# Copyright (c) 2019 Brent Rubell for Adafruit
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
`digitalio`
==============================
DigitalIO for ESP32 over SPI.

* Author(s): Brent Rubell
"""
from micropython import const

# Enums
class DriveMode():
    PUSH_PULL = None
    OPEN_DRAIN = None

DriveMode.PUSH_PULL = DriveMode()
DriveMode.OPEN_DRAIN = DriveMode()

class Direction:
    INPUT = None
    OUTPUT = None

Direction.INPUT = Direction()
Direction.OUTPUT = Direction()

class Pin:
    IN = const(0x00)
    OUT = const(0x01)
    LOW = const(0x00)
    HIGH = const(0x01)
    id = None
    _value = LOW
    _mode = IN

    ESP32_GPIO_PINS = set([0, 1, 2, 4, 5,
                            12, 13, 14, 15,
                            16, 17, 18, 19,
                            21, 22, 23, 25,
                            26, 27, 32, 33])

    def __init__(self, esp_pin, esp):
        if esp_pin in self.ESP32_GPIO_PINS:
            self.id = esp_pin
        else:
            raise AttributeError("Pin %d is not a valid ESP32 GPIO Pin."%esp_pin)
        self._esp = esp

    def init(self, mode=IN):
        """Initalizes a pre-defined pin.
        :param mode: Pin mode (IN, OUT, LOW, HIGH).
        """
        print('pin init')
        if mode != None:
            if mode == self.IN:
                self._mode = self.IN
                self._esp.set_pin_mode(self.id, 0)
            elif mode == self.OUT:
                self._mode = self.OUT
                self._esp.set_pin_mode(self.id, 1)
            else:
                raise RuntimeError("Invalid mode defined")

    def value(self, val=None):
        """Sets ESP32 Pin GPIO output mode.
        :param val: Output level (LOW, HIGH)
        """
        if val != None:
            if val == self.LOW:
                self._value = val
                self._esp.set_digital_write(self.id, 0)
            elif val == self.HIGH:
                self._value = val
                self._esp.set_digital_write(self.id, 1)
            else:
                raise RuntimeError("Invalid value for pin")
        else:
            raise NotImplementedError("digitalRead not currently implemented in esp32spi")

    def __repr__(self):
        return str(self.id)

class DigitalInOut():

    """Mock DigitalIO CircuitPython API Implementation for ESP32SPI.
    Provides access to ESP_SPIcontrol methods.
    """
    _pin = None
    def __init__(self, esp, pin):
        self._esp = esp
        self._pin = Pin(pin, self._esp)
        print('id:', self._pin.id)
        self._direction = Direction.INPUT

    def deinit(self):
        self._pin = None
    
    def __exit__(self):
        self.deinit()

    @property
    def direction(self):
        return self.__direction

    @direction.setter
    def direction(self, dir):
        self.__direction = dir
        if dir is Direction.OUTPUT:
            self._pin.init(mode=Pin.OUT)
            self.value = False
            self.drive_mode = DriveMode.PUSH_PULL
        elif dir is Direction.INPUT:
            self._pin.init(mode=Pin.IN)
        else:
            raise AttributeError("Not a Direction")

    @property
    def value(self):
        return self._pin.value() is 1

    @value.setter
    def value(self, val):
        if self.direction is Direction.OUTPUT:
            self._pin.value(1 if val else 0)
        else:
            raise AttributeError("Not an output")

    @property
    def drive_mode(self):
        if self.direction is Direction.OUTPUT:
            return self.__drive_mode
        else:
            raise AttributeError("Not an output")

    @drive_mode.setter
    def drive_mode(self, mode):
        self.__drive_mode = mode
        if mode is DriveMode.OPEN_DRAIN:
            self._pin.init(mode=Pin.OPEN_DRAIN)
        elif mode is DriveMode.PUSH_PULL:
            self._pin.init(mode=Pin.OUT)