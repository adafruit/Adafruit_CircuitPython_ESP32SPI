# SPDX-FileCopyrightText: 2020 Bryan Siepert for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
from digitalio import DigitalInOut
import neopixel
from adafruit_io.adafruit_io import IO_HTTP
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise


class Timer:
    """A class to track timeouts, like an egg timer"""

    def __init__(self, timeout=0.0):
        self._timeout = None
        self._start_time = None
        if timeout:
            self.rewind_to(timeout)

    @property
    def expired(self):
        """Returns the expiration status of the timer
        Returns:
            bool: True if more than `timeout` seconds has past since it was set
        """
        return (time.monotonic() - self._start_time) > self._timeout

    def rewind_to(self, new_timeout):
        """Re-wind the timer to a new timeout and start ticking"""
        self._timeout = float(new_timeout)
        self._start_time = time.monotonic()


class IntervalToggler:
    def __init__(self, interval=0.3):
        self._interval = interval
        self._toggle_state = False
        self._timer = Timer(self._interval)

    def update_toggle(self):
        if self._timer.expired:
            self._toggle_state = not self._toggle_state
            print("Toggle!", self._toggle_state)
            self._timer.rewind_to(self._interval)


toggler = IntervalToggler(interval=0.5)

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

# Create the ESP32SPI class that communicates with the Airlift Module over SPI
# Pass in a service function to be called while waiting for the ESP32 status to update

esp = adafruit_esp32spi.ESP_SPIcontrol(
    board.SPI(),
    esp32_cs,
    esp32_ready,
    esp32_reset,
    service_function=toggler.update_toggle,
)

status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)

wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

# Create an instance of the Adafruit IO HTTP client
io = IO_HTTP(aio_username, aio_key, wifi)

time_timer = Timer(15.0)
while True:
    # You can remove the service function keyword argument to compare
    toggler.update_toggle()

    if time_timer.expired:
        try:
            print("Current time:", io.receive_time())
        except RuntimeError as e:
            print("whoops! An error recurred, trying again")
            # rewind to 0 to try again immediately
            time_timer.rewind_to(0.0)
            continue
        time_timer.rewind_to(15.0)
