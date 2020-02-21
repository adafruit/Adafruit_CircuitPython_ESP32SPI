# Using ESP32 co-processor GPIO pins with CircuitPython ESP32SPI

## Available pins

```
    # ESP32_GPIO_PINS:
    # https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI/blob/master/adafruit_esp32spi/digitalio.py
    # 0, 1, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39
    #
    # Pins Used for ESP32SPI
    #             5,         14,             18,             23,                 33

    # Avialable ESP32SPI Outputs (digital or 'analog' PWM) with NINA FW >= 1.3.1
    #
    # Adafruit ESP32 Breakout
    # *,    2, 4,    12,  R,     15, 16, 17,     19, 21, 22,     25, 26, 27, 32
    # Adafruit ESP32 Feather
    #          4,    12,  R,     15, 16, 17,     19, 21, 22,     25, 26, 27, 32
    # TinyPICO
    #          4,                15,             19, 21, 22,     25, 26, 27, 32
    # Adafruit ESP32 Airlift Breakout†
    #                                                             G,  R,  B
    # Adafruit ESP32 Airlift Feather†
    #                                                             G,  R,  B
    # Adafruit ESP32 Airlift Bitsy Add-On†
    #                                                             G,  R,  B

    # Avialable† ESP32SPI Digital Inputs with NINA FW >= 1.5.0
    #
    # Adafruit ESP32 Breakout
    # *,    2, 4,    12,  R,     15, 16, 17,     19, 21, 22,     25, 26, 27, 32,     34, 35, 36, 39
    # Adafruit ESP32 Feather
    #          4,    12,  R,     15, 16, 17,     19, 21, 22,     25, 26, 27, 32,     34,     36, 39
    # TinyPICO
    #          4,                15,             19, 21, 22,     25, 26, 27, 32      CH

    # Avialable ESP32SPI Analog Inputs (ADC1) with NINA FW >= 1.5.0
    #
    # Adafruit ESP32 Breakout
    # *,                                                                     32,     34, 35, HE, HE
    # Adafruit ESP32 Feather
    # *,                                                                     32,     34, BA, HE, HE
    # TinyPICO
    #                                                                        32,         BA

Notes:
 *  Used for bootloading
 G  Green LED
 R  Red LED
 B  Blue LED
BA  On-board connection to battery via 50:50 voltage divider
CH  Battery charging state (digital pin)
HE  Hall Effect sensor
```

Note that on the Airlift FeatherWing and the Airlift Bitsy Add-On, the ESP32 SPI Chip Select (CS) pin aligns with M4's D13 Red LED pin:
```
    esp32_cs = DigitalInOut(board.D13)  # M4 Red LED
    esp32_ready = DigitalInOut(board.D11)
    esp32_reset = DigitalInOut(board.D12)
```
So the Red LED on the main Feather processor will almost always appear to be ON or slightly flickering when ESP32SPI is running.

## ESP32 Reset

Because the ESP32 can sometimes reset without indication to the CircuitPython code, putting ESP32 GPIO pins into input mode, `esp.set_digital_write(pin, val)` should be preceded by `esp.set_pin_mode(pin, 0x1)`, with appropriate error handling. Other non-default `esp` states (e.g., `esp.set_esp_debug()`) will also get re-initialized to default settings upon ESP32 reset, so CircuitPython code should anticipate this.

## GPIO on Airlift add-on boards

It should also be possible to do ESP32SPI reads and writes on the Airlift add-on boards, but other than the SPI pins and the green, blue, and red LEDs, the only pins available are RX (GPIO3), TX (GPIO1), and GPIO0, so function is very limited. Analog input is ruled out since none of those pins are on ADC1.

The Airlift Breakout has level-shifting on RX and GPIO0, so those could be digital inputs only. TX could be used as a digital input or as a digital or analog (PWM) output.

The Airlift FeatherWing and Bitsy Add-On have no level-shifting since they're designed to be stacked onto their associated M4 microcontrollers, so theoretically RX, TX, and GPIO0 could be used as digital inputs, or as digital or analog (PWM) outputs. It's hard to find a use case for doing this when stacked since RX, TX, and GPIO0 will be connected to M4 GPIO pins.

The Airlift Shield has level-shifting on RX and GPIO0, with stacking issues similar to the wings.

The RX, TX, and GPIO0 pins are used for updating the NINA firmware, and have specific behaviors immediately following reboot that need to be considered if reusing them as GPIO. On the Airlift FeatherWing and Bitsy Add-On, there are pads that need to be soldered to connect the pins. NINA does output messages to TX when connected, depending on the esp debug level set.

Ultimately it makes the most sense to use a non-stacked full-pinout ESP32 as co-processor for ESP32SPI pin read and write features.
