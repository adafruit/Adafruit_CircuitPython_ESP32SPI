# SPDX-FileCopyrightText: Copyright (c) 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`PWMOut`
==============================
PWMOut CircuitPython API for ESP32SPI.

* Author(s): Brent Rubell
"""


class PWMOut:
    """
    Implementation of CircuitPython PWMOut for ESP32SPI.

    :param int esp_pin: Valid ESP32 GPIO Pin, predefined in ESP32_GPIO_PINS.
    :param ESP_SPIcontrol esp: The ESP object we are using.
    :param int duty_cycle: The fraction of each pulse which is high, 16-bit.
    :param int frequency: The target frequency in Hertz (32-bit).
    :param bool variable_frequency: True if the frequency will change over time.
    """

    ESP32_PWM_PINS = set(
        [0, 1, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33]
    )

    def __init__(self, esp, pwm_pin, *, frequency=500, duty_cycle=0, variable_frequency=False):
        if pwm_pin in self.ESP32_PWM_PINS:
            self._pwm_pin = pwm_pin
        else:
            raise AttributeError("Pin %d is not a valid ESP32 GPIO Pin." % pwm_pin)
        self._esp = esp
        self._duty_cycle = duty_cycle
        self._freq = frequency
        self._var_freq = variable_frequency

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.deinit()

    def deinit(self):
        """De-initalize the PWMOut object."""
        self._duty_cycle = 0
        self._freq = 0
        self._pwm_pin = None

    def _is_deinited(self):
        """Checks if PWMOut object has been previously de-initalized"""
        if self._pwm_pin is None:
            raise ValueError(
                "PWMOut Object has been deinitialized and can no longer "
                "be used. Create a new PWMOut object."
            )

    @property
    def duty_cycle(self):
        """Returns the PWMOut object's duty cycle as a
        ratio from 0.0 to 1.0."""
        self._is_deinited()
        return self._duty_cycle

    @duty_cycle.setter
    def duty_cycle(self, duty_cycle):
        """Sets the PWMOut duty cycle.
        :param float duty_cycle: Between 0.0 (low) and 1.0 (high).
        :param int duty_cycle: Between 0 (low) and 1 (high).
        """
        self._is_deinited()
        if not isinstance(duty_cycle, (int, float)):
            raise TypeError("Invalid duty_cycle, should be int or float.")
        duty_cycle /= 65535.0
        if not 0.0 <= duty_cycle <= 1.0:
            raise ValueError("Invalid duty_cycle, should be between 0.0 and 1.0")
        self._esp.set_analog_write(self._pwm_pin, duty_cycle)

    @property
    def frequency(self):
        """Returns the PWMOut object's frequency value."""
        self._is_deinited()
        return self._freq

    @frequency.setter
    def frequency(self, freq):
        """Sets the PWMOut object's frequency value.
        :param int freq: 32-bit value that dictates the PWM frequency in Hertz.
        NOTE: Only writeable when constructed with variable_Frequency=True.
        """
        self._is_deinited()
        self._freq = freq
        raise NotImplementedError("PWMOut Frequency not implemented in ESP32SPI")
