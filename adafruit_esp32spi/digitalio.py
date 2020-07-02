# SPDX-FileCopyrightText: Copyright (c) 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`digitalio`
==============================
DigitalIO for ESP32 over SPI.

* Author(s): Brent Rubell, based on Adafruit_Blinka digitalio implementation
and bcm283x Pin implementation.
https://github.com/adafruit/Adafruit_Blinka/blob/master/src/adafruit_blinka/microcontroller/bcm283x/pin.py
https://github.com/adafruit/Adafruit_Blinka/blob/master/src/digitalio.py
"""
from micropython import const


class Pin:
    """
    Implementation of CircuitPython API Pin Handling
    for ESP32SPI.

    :param int esp_pin: Valid ESP32 GPIO Pin, predefined in ESP32_GPIO_PINS.
    :param ESP_SPIcontrol esp: The ESP object we are using.

    NOTE: This class does not currently implement reading digital pins
    or the use of internal pull-up resistors.
    """

    # pylint: disable=invalid-name
    IN = const(0x00)
    OUT = const(0x01)
    LOW = const(0x00)
    HIGH = const(0x01)
    _value = LOW
    _mode = IN
    pin_id = None

    ESP32_GPIO_PINS = set(
        [0, 1, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33]
    )

    def __init__(self, esp_pin, esp):
        if esp_pin in self.ESP32_GPIO_PINS:
            self.pin_id = esp_pin
        else:
            raise AttributeError("Pin %d is not a valid ESP32 GPIO Pin." % esp_pin)
        self._esp = esp

    def init(self, mode=IN):
        """Initalizes a pre-defined pin.
        :param mode: Pin mode (IN, OUT, LOW, HIGH). Defaults to IN.
        """
        if mode is not None:
            if mode == self.IN:
                self._mode = self.IN
                self._esp.set_pin_mode(self.pin_id, 0)
            elif mode == self.OUT:
                self._mode = self.OUT
                self._esp.set_pin_mode(self.pin_id, 1)
            else:
                raise RuntimeError("Invalid mode defined")

    def value(self, val=None):
        """Sets ESP32 Pin GPIO output mode.
        :param val: Pin output level (LOW, HIGH)
        """
        if val is not None:
            if val == self.LOW:
                self._value = val
                self._esp.set_digital_write(self.pin_id, 0)
            elif val == self.HIGH:
                self._value = val
                self._esp.set_digital_write(self.pin_id, 1)
            else:
                raise RuntimeError("Invalid value for pin")
        else:
            raise NotImplementedError(
                "digitalRead not currently implemented in esp32spi"
            )

    def __repr__(self):
        return str(self.pin_id)


# pylint: disable = too-few-public-methods
class DriveMode:
    """DriveMode Enum."""

    PUSH_PULL = None
    OPEN_DRAIN = None


DriveMode.PUSH_PULL = DriveMode()
DriveMode.OPEN_DRAIN = DriveMode()


class Direction:
    """DriveMode Enum."""

    INPUT = None
    OUTPUT = None


Direction.INPUT = Direction()
Direction.OUTPUT = Direction()


class DigitalInOut:
    """Implementation of DigitalIO module for ESP32SPI.

    :param ESP_SPIcontrol esp: The ESP object we are using.
    :param int pin: Valid ESP32 GPIO Pin, predefined in ESP32_GPIO_PINS.
    """

    _pin = None
    # pylint: disable = attribute-defined-outside-init
    def __init__(self, esp, pin):
        self._esp = esp
        self._pin = Pin(pin, self._esp)
        self.direction = Direction.INPUT

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.deinit()

    def deinit(self):
        """De-initializes the pin object."""
        self._pin = None

    def switch_to_output(self, value=False, drive_mode=DriveMode.PUSH_PULL):
        """Set the drive mode and value and then switch to writing out digital values.
        :param bool value: Default mode to set upon switching.
        :param DriveMode drive_mode: Drive mode for the output.
        """
        self._direction = Direction.OUTPUT
        self._drive_mode = drive_mode
        self.value = value

    def switch_to_input(self, pull=None):
        """Sets the pull and then switch to read in digital values.
        :param Pull pull: Pull configuration for the input.
        """
        raise NotImplementedError(
            "Digital reads are not currently supported in ESP32SPI."
        )

    @property
    def direction(self):
        """Returns the pin's direction."""
        return self.__direction

    @direction.setter
    def direction(self, pin_dir):
        """Sets the direction of the pin.
        :param Direction dir: Pin direction (Direction.OUTPUT or Direction.INPUT)
        """
        self.__direction = pin_dir
        if pin_dir is Direction.OUTPUT:
            self._pin.init(mode=Pin.OUT)
            self.value = False
            self.drive_mode = DriveMode.PUSH_PULL
        elif pin_dir is Direction.INPUT:
            self._pin.init(mode=Pin.IN)
        else:
            raise AttributeError("Not a Direction")

    @property
    def value(self):
        """Returns the digital logic level value of the pin."""
        return self._pin.value() == 1

    @value.setter
    def value(self, val):
        """Sets the digital logic level of the pin.
        :param type value: Pin logic level.
        :param int value: Pin logic level. 1 is logic high, 0 is logic low.
        :param bool value: Pin logic level. True is logic high, False is logic low.
        """
        if self.direction is Direction.OUTPUT:
            self._pin.value(1 if val else 0)
        else:
            raise AttributeError("Not an output")

    @property
    def drive_mode(self):
        """Returns pin drive mode."""
        if self.direction is Direction.OUTPUT:
            return self._drive_mode
        raise AttributeError("Not an output")

    @drive_mode.setter
    def drive_mode(self, mode):
        """Sets the pin drive mode.
        :param DriveMode mode: Defines the drive mode when outputting digital values.
        Either PUSH_PULL or OPEN_DRAIN
        """
        self.__drive_mode = mode
        if mode is DriveMode.OPEN_DRAIN:
            raise NotImplementedError(
                "Drive mode %s not implemented in ESP32SPI." % mode
            )
        if mode is DriveMode.PUSH_PULL:
            self._pin.init(mode=Pin.OUT)
