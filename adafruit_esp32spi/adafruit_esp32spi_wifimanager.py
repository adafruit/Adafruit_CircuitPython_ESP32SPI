# The MIT License (MIT)
#
# Copyright (c) 2019 Melissa LeBlanc-Williams for Adafruit Industries
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
`adafruit_esp32spi_wifimanager`
================================================================================

WiFi Manager for making ESP32 SPI as WiFi much easier

* Author(s): Melissa LeBlanc-Williams
"""

import neopixel
import adafruit_esp32spi.adafruit_esp32spi_requests as requests

class ESPSPI_WiFiManager:
    """
    A class to help manage the Wifi connection
    """
    def __init__(self, esp, settings, status_neopixel=None):
        # Read the settings
        self._esp = esp
        self.debug = False
        self.ssid = settings['ssid']
        self.password = settings['password']
        requests.set_interface(self._esp)
        if status_neopixel:
            self.neopix = neopixel.NeoPixel(status_neopixel, 1, brightness=0.2)
        else:
            self.neopix = None
        self.neo_status(0)

    def connect(self):
        if self.debug:
            if self._esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
                print("ESP32 found and in idle mode")
            print("Firmware vers.", self._esp.firmware_version)
            print("MAC addr:", [hex(i) for i in self._esp.MAC_address])
            for ap in self._esp.scan_networks():
                print("\t%s\t\tRSSI: %d" % (str(ap['ssid'], 'utf-8'), ap['rssi']))
        while not self._esp.is_connected:
            try:
                if self.debug:
                    print("Connecting to AP...")
                self.neo_status((100, 0, 0))
                self._esp.connect_AP(bytes(self.ssid,'utf-8'), bytes(self.password,'utf-8'))
                self.neo_status((0, 100, 0))
            except (ValueError, RuntimeError) as e:
                if self.debug:
                    print("Failed to connect, retrying\n", e)
                continue

    def get(self, url, **kw):
        self.neo_status((100, 100, 0))
        return_val = requests.get(url, **kw)
        self.neo_status((0, 0, 100))
        return return_val

    def post(self, url, **kw):
        self.neo_status((100, 100, 0))
        return_val = requests.post(url, **kw)
        self.neo_status((0, 0, 100))
        return return_val

    def ping(self, host):
        #Blink the LED Green
        #Send Stuff to Requests
        #stop Blinking LED
        #Return Result
        return None

    def neo_status(self, value):
        if self.neopix:
            self.neopix.fill(value)
