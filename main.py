import time                   # Allows use of time.sleep() for delays
from mqtt import MQTTClient   # For use of MQTT protocol to talk to Adafruit IO
import ubinascii              # Conversions between binary data and various encodings
import machine                # Interfaces with hardware components
import micropython            # Needed to run any MicroPython code
import random                 # Random number generator
from machine import Pin       # Define pin
import dht


# BEGIN SETTINGS
# These need to be change to suit your environment
RANDOMS_INTERVAL = 20000    # milliseconds
last_random_sent_ticks = 0  # milliseconds
led = Pin("LED", Pin.OUT)   # led pin initialization for Raspberry Pi Pico W

# Wireless network
WIFI_SSID = "Sreehas Sreejith_IoT_LNU"
WIFI_PASS = "st223gk" # No this is not my regular password. :)

# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "sreehassreejith"
AIO_KEY = "aio_djTt40CRiUdyDqC4BuAkykLIm0i7"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # Can be anything
AIO_LIGHTS_FEED = "sreehassreejith/feeds/lights"
AIO_RANDOMS_FEED = "sreehassreejith/feeds/randoms"

# END SETTINGS



# FUNCTIONS
dh = dht.DHT11(Pin(27))
dh.measure()
temp = dh.temperature()
hum = dh.humidity()
msg_temp = "The temperature is " + str(temp) + 'C'
msg_hum = "The humidity is %d%%" % hum
print(msg_temp)
print(msg_hum)
# Function to connect Pico to the WiFi
def do_connect():
    
    import network
    from time import sleep
    import machine
    wlan = network.WLAN(network.STA_IF)         # Put modem on Station mode

    if not wlan.isconnected():                  # Check if already connected
        print('connecting to network...')
        wlan.active(True)                       # Activate network interface
        # set power mode to get WiFi power-saving off (if needed)
        wlan.config(pm = 0xa11140)
        wlan.connect(WIFI_SSID, WIFI_PASS)  # Your WiFi Credential
        print('Waiting for connection...', end='')
        # Check if it is connected otherwise wait
        while not wlan.isconnected() and wlan.status() >= 0:
            print('.', end='')
            sleep(1)
    # Print the IP assigned by router
    ip = wlan.ifconfig()[0]
    print('\nConnected on {}'.format(ip))
    return ip 



# Callback Function to respond to messages from Adafruit IO
def sub_cb(topic, msg):          # sub_cb means "callback subroutine"
    print((topic, msg))          # Outputs the message that was received. Debugging use.
    if msg == b"ON":             # If message says "ON" ...
        led.on()                 # ... then LED on
    elif msg == b"OFF":          # If message says "OFF" ...
        led.off()                # ... then LED off


# Function to generate a random number between 0 and the upper_bound
def random_integer(upper_bound):
    return random.getrandbits(32) % upper_bound

# Function to publish random number to Adafruit IO MQTT server at fixed interval
def send_random():
    global last_random_sent_ticks
    global RANDOMS_INTERVAL

    if ((time.ticks_ms() - last_random_sent_ticks) < RANDOMS_INTERVAL):
        return; # Too soon since last one sent.

    some_number = random_integer(100)
    print("Publishing: {0} to {1} ... ".format(temp, AIO_RANDOMS_FEED))
    print("Publishing: {0} to {1} ... ".format(hum, AIO_LIGHTS_FEED), end='')
    try:
        msgTmp = str(temp) + 'C'
        msgHum = str(hum) + '%'
        client.publish(topic=AIO_RANDOMS_FEED, msg=msgTmp)
        client.publish(topic=AIO_LIGHTS_FEED, msg=msgHum)
        print("DONE")
    except Exception as e:
        print("FAILED")
    finally:
        last_random_sent_ticks = time.ticks_ms()


# Try WiFi Connection
try:
    ip = do_connect()
except KeyboardInterrupt:
    print("Keyboard interrupt")

# Use the MQTT protocol to connect to Adafruit IO
client = MQTTClient(AIO_CLIENT_ID, AIO_SERVER, AIO_PORT, AIO_USER, AIO_KEY)

# Subscribed messages will be delivered to this callback
client.set_callback(sub_cb)
client.connect()
client.subscribe(AIO_LIGHTS_FEED)
client.subscribe(AIO_RANDOMS_FEED)
print("Connected to %s, subscribed to %s topic" % (AIO_SERVER, AIO_LIGHTS_FEED)) 



try:                      # Code between try: and finally: may cause an error
                          # so ensure the client disconnects the server if
                          # that happens.
    while 1:              # Repeat this loop forever
        client.check_msg()# Action a message if one is received. Non-blocking.
        send_random()     # Send a random number to Adafruit IO if it's time.
finally:                  # If an exception is thrown ...
    client.disconnect()   # ... disconnect the client and clean up.
    client = None
    print("Disconnected from Adafruit IO.")

