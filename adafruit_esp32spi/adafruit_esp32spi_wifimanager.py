# SPDX-FileCopyrightText: Copyright (c) 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_esp32spi_wifimanager`
================================================================================

WiFi Manager for making ESP32 SPI as WiFi much easier

* Author(s): Melissa LeBlanc-Williams, ladyada
"""

# pylint: disable=no-name-in-module

import warnings
from time import sleep
from micropython import const
import adafruit_connection_manager
import adafruit_requests
from adafruit_esp32spi import adafruit_esp32spi


# pylint: disable=too-many-instance-attributes
class WiFiManager:
    """
    A class to help manage the Wifi connection
    """

    NORMAL = const(1)
    ENTERPRISE = const(2)

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        esp,
        ssid,
        password=None,
        *,
        enterprise_ident=None,
        enterprise_user=None,
        status_pixel=None,
        attempts=2,
        connection_type=NORMAL,
        debug=False,
    ):
        """
        :param ESP_SPIcontrol esp: The ESP object we are using
        :param str ssid: the SSID of the access point. Must be less than 32 chars.
        :param str password: the password for the access point. Must be 8-63 chars.
        :param str enterprise_ident: the ident to use when connecting to an enterprise access point.
        :param str enterprise_user: the username to use when connecting to an enterprise access
            point.
        :param status_pixel: (Optional) The pixel device - A NeoPixel, DotStar,
            or RGB LED (default=None). The status LED, if given, turns red when
            attempting to connect to a Wi-Fi network or create an access point,
            turning green upon success. Additionally, if given, it will turn blue
            when attempting an HTTP method or returning IP address, turning off
            upon success.
        :type status_pixel: NeoPixel, DotStar, or RGB LED
        :param int attempts: (Optional) Failed attempts before resetting the ESP32 (default=2)
        :param const connection_type: (Optional) Type of WiFi connection: NORMAL or ENTERPRISE
        """
        # Read the settings
        self.esp = esp
        self.debug = debug
        self.ssid = ssid
        self.password = password
        self.attempts = attempts
        self._connection_type = connection_type
        self.statuspix = status_pixel
        self.pixel_status(0)
        self._ap_index = 0

        # create requests session
        pool = adafruit_connection_manager.get_radio_socketpool(self.esp)
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(self.esp)
        self._requests = adafruit_requests.Session(pool, ssl_context)

        # Check for WPA2 Enterprise values
        self.ent_ssid = ssid
        self.ent_ident = enterprise_ident
        self.ent_user = enterprise_user
        self.ent_password = password

    # pylint: enable=too-many-arguments

    def reset(self):
        """
        Perform a hard reset on the ESP32
        """
        if self.debug:
            print("Resetting ESP32")
        self.esp.reset()

    def connect(self):
        """
        Attempt to connect to WiFi using the current settings
        """
        if self.debug:
            if self.esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
                print("ESP32 found and in idle mode")
            print("Firmware vers.", self.esp.firmware_version)
            print("MAC addr:", [hex(i) for i in self.esp.MAC_address])
            for access_pt in self.esp.scan_networks():
                print("\t%s\t\tRSSI: %d" % (access_pt.ssid, access_pt.rssi))
        if self._connection_type == WiFiManager.NORMAL:
            self.connect_normal()
        elif self._connection_type == WiFiManager.ENTERPRISE:
            self.connect_enterprise()
        else:
            raise TypeError("Invalid WiFi connection type specified")

    def _get_next_ap(self):
        if isinstance(self.ssid, (tuple, list)) and isinstance(
            self.password, (tuple, list)
        ):
            if not self.ssid or not self.password:
                raise ValueError("SSID and Password should contain at least 1 value")
            if len(self.ssid) != len(self.password):
                raise ValueError("The length of SSIDs and Passwords should match")
            access_point = (self.ssid[self._ap_index], self.password[self._ap_index])
            self._ap_index += 1
            if self._ap_index >= len(self.ssid):
                self._ap_index = 0
            return access_point
        if isinstance(self.ssid, (tuple, list)) or isinstance(
            self.password, (tuple, list)
        ):
            raise NotImplementedError(
                "If using multiple passwords, both SSID and Password should be lists or tuples"
            )
        return (self.ssid, self.password)

    def connect_normal(self):
        """
        Attempt a regular style WiFi connection.
        """
        failure_count = 0
        (ssid, password) = self._get_next_ap()
        while not self.esp.is_connected:
            try:
                if self.debug:
                    print("Connecting to AP...")
                self.pixel_status((100, 0, 0))
                self.esp.connect_AP(bytes(ssid, "utf-8"), bytes(password, "utf-8"))
                failure_count = 0
                self.pixel_status((0, 100, 0))
            except OSError as error:
                print("Failed to connect, retrying\n", error)
                failure_count += 1
                if failure_count >= self.attempts:
                    failure_count = 0
                    (ssid, password) = self._get_next_ap()
                    self.reset()
                continue

    def create_ap(self):
        """
        Attempt to initialize in Access Point (AP) mode.
        Uses SSID and optional passphrase from the current settings
        Other WiFi devices will be able to connect to the created Access Point
        """
        failure_count = 0
        while not self.esp.ap_listening:
            try:
                if self.debug:
                    print("Waiting for AP to be initialized...")
                self.pixel_status((100, 0, 0))
                if self.password:
                    self.esp.create_AP(
                        bytes(self.ssid, "utf-8"), bytes(self.password, "utf-8")
                    )
                else:
                    self.esp.create_AP(bytes(self.ssid, "utf-8"), None)
                failure_count = 0
                self.pixel_status((0, 100, 0))
            except OSError as error:
                print("Failed to create access point\n", error)
                failure_count += 1
                if failure_count >= self.attempts:
                    failure_count = 0
                    self.reset()
                continue
        print("Access Point created! Connect to ssid:\n {}".format(self.ssid))

    def connect_enterprise(self):
        """
        Attempt an enterprise style WiFi connection
        """
        failure_count = 0
        self.esp.wifi_set_network(bytes(self.ent_ssid, "utf-8"))
        self.esp.wifi_set_entidentity(bytes(self.ent_ident, "utf-8"))
        self.esp.wifi_set_entusername(bytes(self.ent_user, "utf-8"))
        self.esp.wifi_set_entpassword(bytes(self.ent_password, "utf-8"))
        self.esp.wifi_set_entenable()
        while not self.esp.is_connected:
            try:
                if self.debug:
                    print(
                        "Waiting for the ESP32 to connect to the WPA2 Enterprise AP..."
                    )
                self.pixel_status((100, 0, 0))
                sleep(1)
                failure_count = 0
                self.pixel_status((0, 100, 0))
                sleep(1)
            except OSError as error:
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
        if not self.esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = self._requests.get(url, **kw)
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
        if not self.esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = self._requests.post(url, **kw)
        self.pixel_status(0)
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
        if not self.esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = self._requests.put(url, **kw)
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
        if not self.esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = self._requests.patch(url, **kw)
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
        if not self.esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        return_val = self._requests.delete(url, **kw)
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
        if not self.esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        response_time = self.esp.ping(host, ttl=ttl)
        self.pixel_status(0)
        return response_time

    def ip_address(self):
        """
        Returns a formatted local IP address, update status pixel.
        """
        if not self.esp.is_connected:
            self.connect()
        self.pixel_status((0, 0, 100))
        self.pixel_status(0)
        return self.esp.ipv4_address

    def pixel_status(self, value):
        """
        Change Status Pixel if it was defined

        :param value: The value to set the Board's status LED to
        :type value: int or 3-value tuple
        """
        if self.statuspix:
            if hasattr(self.statuspix, "color"):
                self.statuspix.color = value
            else:
                self.statuspix.fill(value)

    def signal_strength(self):
        """
        Returns receiving signal strength indicator in dBm
        """
        if not self.esp.is_connected:
            self.connect()
        return self.esp.ap_info.rssi


# pylint: disable=too-many-instance-attributes
class ESPSPI_WiFiManager(WiFiManager):
    """
    A legacy class to help manage the Wifi connection. Please update to using WiFiManager
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        esp,
        secrets,
        status_pixel=None,
        attempts=2,
        connection_type=WiFiManager.NORMAL,
        debug=False,
    ):
        """
        :param ESP_SPIcontrol esp: The ESP object we are using
        :param dict secrets: The WiFi secrets dict
            The use of secrets.py to populate the secrets dict is deprecated
            in favor of using settings.toml.
        :param status_pixel: (Optional) The pixel device - A NeoPixel, DotStar,
            or RGB LED (default=None). The status LED, if given, turns red when
            attempting to connect to a Wi-Fi network or create an access point,
            turning green upon success. Additionally, if given, it will turn blue
            when attempting an HTTP method or returning IP address, turning off
            upon success.
        :type status_pixel: NeoPixel, DotStar, or RGB LED
        :param int attempts: (Optional) Failed attempts before resetting the ESP32 (default=2)
        :param const connection_type: (Optional) Type of WiFi connection: NORMAL or ENTERPRISE
        """

        warnings.warn(
            "ESP32WiFiManager, which uses `secrets`, is deprecated. Use WifiManager instead and "
            "fetch values from settings.toml with `os.getenv()`."
        )

        super().__init__(
            esp=esp,
            ssid=secrets.get("ssid"),
            password=secrets.get("password"),
            enterprise_ident=secrets.get("ent_ident", ""),
            enterprise_user=secrets.get("ent_user"),
            status_pixel=status_pixel,
            attempts=attempts,
            connection_type=connection_type,
            debug=debug,
        )
