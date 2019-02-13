
import time
import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_requests as requests


print("ESP32 SPI webclient test")

# Get wifi details and more from a settings.py file
try:
    from esp32spi_settings import settings
except ImportError:
    print("WiFi settings are kept in settings.py, please add them there!")
    raise


esp32_cs = DigitalInOut(board.D9)
esp32_ready = DigitalInOut(board.D10)
esp32_reset = DigitalInOut(board.D5)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

requests.set_interface(esp)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])
for ap in esp.scan_networks():
    print("\t%s\t\tRSSI: %d" % (str(ap['ssid'], 'utf-8'), ap['rssi']))
while not esp.is_connected:
    try:
        print("Connecting to AP...")
        esp.connect_AP(bytes(settings['ssid'],'utf-8'), bytes(settings['password'],'utf-8'))
    except (ValueError, RuntimeError) as e:
        print("Failed to connect, retrying\n", e)
        continue
print("Connected to", str(esp.ssid, 'utf-8'), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))


counter = 0
while True:
    try:
        while not esp.is_connected:
            # settings dictionary must contain 'ssid' and 'password' at a minimum
            esp.connect_AP(bytes(settings['ssid'],'utf-8'), bytes(settings['password'],'utf-8'))
        # great, lets get the data
        print("Posting data...", end='')
        data=counter
        feed='test'
        payload={'value':data}
        response=requests.post(
            "https://io.adafruit.com/api/v2/"+settings['aio_username']+"/feeds/"+feed+"/data",
            json=payload,headers={bytes("X-AIO-KEY","utf-8"):bytes(settings['aio_key'],"utf-8")})
        print(response.json())
        response.close()
        counter = counter + 1
        print("OK")
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        continue
    response = None
    time.sleep(15)
