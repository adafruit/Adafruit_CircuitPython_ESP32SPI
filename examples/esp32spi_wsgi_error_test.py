# SPDX-FileCopyrightText: 2019 Alec Delaney
# SPDX-License-Identifier: MIT

import board
from digitalio import DigitalInOut
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_wifimanager as wifimanager
import adafruit_esp32spi.adafruit_esp32spi_wsgiserver as server
from adafruit_wsgi.wsgi_app import WSGIApp
import neopixel
from secrets import secrets

# Initialize the neopixels, change the pin, number of neopixels, and pixel
# order according to your device
pixels = neopixel.NeoPixel(board.D2, 5, brightness=0.25, pixel_order=neopixel.RGB)
animation = Rainbow(pixels, speed=0.1, period=0.75)
pixel_status = False

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

# If you have an AirLift Shield:
# esp32_cs = DigitalInOut(board.D10)
# esp32_ready = DigitalInOut(board.D7)
# esp32_reset = DigitalInOut(board.D5)

# If you have an AirLift Featherwing or ItsyBitsy Airlift:
# esp32_cs = DigitalInOut(board.D13)
# esp32_ready = DigitalInOut(board.D11)
# esp32_reset = DigitalInOut(board.D12)

# If you have an externally connected ESP32:
# NOTE: You may need to change the pins to reflect your wiring
# esp32_cs = DigitalInOut(board.D9)
# esp32_ready = DigitalInOut(board.D10)
# esp32_reset = DigitalInOut(board.D5)

# Create the ESP_SPIcontrol object with the pins
esp32 = adafruit_esp32spi.ESP_SPIcontrol(esp32_cs, esp32_ready, esp32_reset)

# Use the WiFiManager to simplify handing the connection
# NOTE: You can turn debug off if you want!
wifi = wifimanager.ESPSPI_WiFiManager(esp32, secrets, attempts=3, debug=True)
wifi.connect()

# Here we can define the functions we want to be called by the server
# You can use the functionality of `adafruit_esp32spi_wsgiserver`,
# but here we're using `adafruit_wsgi`
web_app = WSGIApp()

# Here we'll define a function that WILL work
@web_app.route("/neopixel/toggle")
def toggle_neopixels(request):
    if pixel_status: # If already playing...
        animation.freeze()
    else: # If already frozen...
        animation.resume()
    return ("200 OK", {"Content-Type", "text/plain"}, "Animation should have toggled!")

# Here we'll define a function that WON'T work
@web_app.route("/neopixel/error")
def error_out(request):
    # We can pretend something went wrong by raising an error
    raise RuntimeError("Uh-oh, something happened!")

# Here we'll actually set up the WSGI server implementation
server.set_interface(esp32)
wsgi_server = server.WSGIServer(80, application=web_app, error_return=("500 Internal Server Error", {"Content-Type", "text/plain"}, "Sorry, looks like something went wrong!"))
wsgi_server.start()

# Show IP address information for usage
pretty_ip_address = esp32.pretty_ip(esp32.ip_address)
print("IP address: {}".format(pretty_ip_address))
print("You can go to the following addresses:")
print("To freeze/resume animation: {}".format(pretty_ip_address + "/neopixel/toggle"))
print("To raise an error: {}".format(pretty_ip_address + "/neopixel/error"))

# Main loop that runs the WSGI sever
while True:

    # Reconnect the Wi-Fi if it gets disconnected
    if not esp32.is_connected:
        while not esp32.is_connected:
            wifi.reset()
            pass

    # Read requests to the WSGI server
    wsgi_server.update_poll()

    # Propogate the LED animation
    animation.animate()
