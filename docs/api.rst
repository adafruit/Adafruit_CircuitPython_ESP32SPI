API Reference
#############

.. automodule:: adafruit_esp32spi.adafruit_esp32spi

.. note::
   As of version 11.0.0, it simpler to import this library and its submodules
   The examples in this documentation use the new import names.
   The old import names are still available, but are deprecated and may be removed in a future release.

Before version 11.0.0, the library was structured like this (not all components are shown):

* ``adafruit_esp32spi``

  * ``adafruit_esp32spi``

    * ``ESP32_SPIcontrol``

  * ``adafruit_esp32spi_socketpool``

    * ``SocketPool``

  * ``adafruit_esp32spi_wifimanager``

    * ``WiFiManager``

.. code:: python

    # Old import scheme
    from adafruit_esp32spi import adafruit_esp32spi
    from adafruit_esp32spi.adafruit_esp32spi_socketpool import SocketPool
    from adafruit_esp32spi.adafruit_esp32spi_wifimanager import WiFiManager

Now, the duplicated top-most name is not needed, and there are shorter names for the submodules.

* ``adafruit_esp32spi``

  * ``ESP32_SPIcontrol``

  * ``socketpool``

    * ``SocketPool``

  * ``wifimanager``

    * ``WiFiManager``

.. code:: python

    # New import scheme
    import adafruit_esp32spi
    from adafruit_esp32spi.socketpool import SocketPool
    from adafruit_esp32spi.wifimanager import WiFiManager


.. automodule:: adafruit_esp32spi
   :imported-members:
   :members:

.. automodule:: adafruit_esp32spi.socketpool
   :imported-members:
   :members:

.. automodule:: adafruit_esp32spi.wifimanager
   :imported-members:
   :members:

.. automodule:: adafruit_esp32spi.digitalio
   :members:

.. automodule:: adafruit_esp32spi.PWMOut
   :members:
