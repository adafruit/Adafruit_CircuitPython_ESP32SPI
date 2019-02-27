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

* Author(s): Melissa LeBlanc-Williams, ladyada
"""

# pylint: disable=no-name-in-module

import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_requests as requests

class ESPSPI_WiFiManager:
    """
    A class to help manage the Wifi connection
    """
    def __init__(self, esp, secrets, status_pixel, attempts=2):
        """
        :param ESP_SPIcontrol esp: The ESP object we are using
        :param dict secrets: The WiFi and Adafruit IO secrets dict (See examples)
        :param status_pixel: (Optional) The pixel device - A NeoPixel or DotStar (default=None)
        :type status_pixel: NeoPixel or DotStar
        :param int attempts: (Optional) Failed attempts before resetting the ESP32 (default=2)
        """
        # Read the settings
        self._esp = esp
        self.debug = False
        self.ssid = secrets['ssid']
        self.password = secrets['password']
        self.attempts = attempts
        requests.set_interface(self._esp)
        self.statuspix = status_pixel
        self.pixel_status(0)

    def reset(self):
        """
        Perform a hard reset on the ESP32
        """
        if self.debug:
            print("Resetting ESP32")
        self._esp.reset()

    def connect(self):
        """
        Attempt to connect to WiFi using the current settings
        """
        if self.debug:
            if self._esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
                print("ESP32 found and in idle mode")
            print("Firmware vers.", self._esp.firmware_version)
            print("MAC addr:", [hex(i) for i in self._esp.MAC_address])
            for access_pt in self._esp.scan_networks():
                print("\t%s\t\tRSSI: %d" % (str(access_pt['ssid'], 'utf-8'), access_pt['rssi']))
        failure_count = 0
        while not self._esp.is_connected:
            try:
                if self.debug:
                    print("Connecting to AP...")
                self.pixel_status((100, 0, 0))
                self._esp.connect_AP(bytes(self.ssid, 'utf-8'), bytes(self.password, 'utf-8'))
                failure_count = 0
                self.pixel_status((0, 100, 0))
            except (ValueError, RuntimeError) as error:
                print("Failed to connect, retrying\n", error)
                failure_count += 1
                if failure_count >= self.attempts:
                    failure_count = 0
                    self.reset()
                continue

    def get(self, url, **kw):
        """
        Pass the Get request to requests and update status LED

        :param str url: The URL to retrieve data from
        :param dict data: (Optional) Form data to submit
        :param dict json: (Optional) JSON data to submit. (Data must be None)
        :param dict header: (Optional) Header data to include
        :param bool stream: (Optional) Whether to stream the Response
        :return: The response from the request
        :rtype: Response
        """
        if not self._esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = requests.get(url, **kw)
        self.pixel_status(0)
        return return_val

    def post(self, url, **kw):
        """
        Pass the Post request to requests and update status LED

        :param str url: The URL to post data to
        :param dict data: (Optional) Form data to submit
        :param dict json: (Optional) JSON data to submit. (Data must be None)
        :param dict header: (Optional) Header data to include
        :param bool stream: (Optional) Whether to stream the Response
        :return: The response from the request
        :rtype: Response
        """
        if not self._esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = requests.post(url, **kw)
        return return_val

    def put(self, url, **kw):
        """
        Pass the put request to requests and update status LED

        :param str url: The URL to PUT data to
        :param dict data: (Optional) Form data to submit
        :param dict json: (Optional) JSON data to submit. (Data must be None)
        :param dict header: (Optional) Header data to include
        :param bool stream: (Optional) Whether to stream the Response
        :return: The response from the request
        :rtype: Response
        """
        if not self._esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = requests.put(url, **kw)
        self.pixel_status(0)
        return return_val

    def patch(self, url, **kw):
        """
        Pass the patch request to requests and update status LED

        :param str url: The URL to PUT data to
        :param dict data: (Optional) Form data to submit
        :param dict json: (Optional) JSON data to submit. (Data must be None)
        :param dict header: (Optional) Header data to include
        :param bool stream: (Optional) Whether to stream the Response
        :return: The response from the request
        :rtype: Response
        """
        if not self._esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = requests.patch(url, **kw)
        self.pixel_status(0)
        return return_val

    def delete(self, url, **kw):
        """
        Pass the delete request to requests and update status LED

        :param str url: The URL to PUT data to
        :param dict data: (Optional) Form data to submit
        :param dict json: (Optional) JSON data to submit. (Data must be None)
        :param dict header: (Optional) Header data to include
        :param bool stream: (Optional) Whether to stream the Response
        :return: The response from the request
        :rtype: Response
        """
        if not self._esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = requests.delete(url, **kw)
        self.pixel_status(0)
        return return_val

    def ping(self, host, ttl=250):
        """
        Pass the Ping request to the ESP32, update status LED, return response time

        :param str host: The hostname or IP address to ping
        :param int ttl: (Optional) The Time To Live in milliseconds for the packet (default=250)
        :return: The response time in milliseconds
        :rtype: int
        """
        if not self._esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        response_time = self._esp.ping(host, ttl=ttl)
        self.pixel_status(0)
        return response_time

    def ip_address(self):
        """
        Returns a formatted local IP address, update status pixel.
        """
        if not self._esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        self.pixel_status(0)
        return self._esp.pretty_ip(self._esp.ip_address)

    def pixel_status(self, value):
        """
        Change Status NeoPixel if it was defined

        :param value: The value to set the Board's status LED to
        :type value: int or 3-value tuple
        """
        if self.statuspix:
            self.statuspix.fill(value)

    def signal_strength(self):
        """
        Returns receiving signal strength indicator in dBm
        """
        if not self._esp.is_connected:
            self.connect()
        return self._esp.rssi()
