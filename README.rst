Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-esp32spi/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/esp32spi/en/latest/
    :alt: Documentation Status

.. image:: https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bundle/main/badges/adafruit_discord.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI/actions/
    :alt: Build Status

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Code Style: Ruff

CircuitPython driver library for using ESP32 as WiFi co-processor using SPI.
The companion firmware `is available on GitHub
<https://github.com/adafruit/nina-fw>`_. Please be sure to check the example code for
any specific firmware version dependencies that may exist.


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Adafruit Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_
* `Adafruit CircuitPython ConnectionManager <https://github.com/adafruit/Adafruit_CircuitPython_ConnectionManager/>`_
* `Adafruit CircuitPython Requests <https://github.com/adafruit/Adafruit_CircuitPython_Requests/>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Installing from PyPI
====================
On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-esp32spi/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-esp32spi

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-esp32spi

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .venv
    source .venv/bin/activate
    pip3 install adafruit-circuitpython-esp32spi

Usage Example
=============

Check the examples folder for various demos for connecting and fetching data!

Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/esp32spi/en/latest/>`_.

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
