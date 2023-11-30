import time
from rpi_ws281x import *
import argparse
import paho.mqtt.client as mqtt

# LED strip configuration:
LED_COUNT      = 15     # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating a signal (try 10)
LED_BRIGHTNESS = 65      # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

note_to_led_index = {
    'A0': 0, 'A\\xe2\\x99\\xaf70': 1, 'B0': 2,
    'C1': 3, 'C\\xe2\\x99\\xaf71': 4, 'D1': 5, 'D\\xe2\\x99\\xaf71': 6, 'E1': 7, 'F1': 8, 'F\\xe2\\x99\\xaf71': 9, 'G1': 10, 'G\\xe2\\x99\\xaf71': 11, 'A1': 12, 'A\\xe2\\x99\\xaf71': 13, 'B1': 14,
    'C2': 15, 'C\\xe2\\x99\\xaf72': 16, 'D2': 17, 'D\\xe2\\x99\\xaf72': 18, 'E2': 19, 'F2': 20, 'F\\xe2\\x99\\xaf72': 21, 'G2': 22, 'G\\xe2\\x99\\xaf72': 23, 'A2': 24, 'A\\xe2\\x99\\xaf72': 25, 'B2': 26,
    'C3': 27, 'C\\xe2\\x99\\xaf73': 28, 'D3': 29, 'D\\xe2\\x99\\xaf73': 30, 'E3': 31, 'F3': 32, 'F\\xe2\\x99\\xaf73': 33, 'G3': 34, 'G\\xe2\\x99\\xaf73': 35, 'A3': 36, 'A\\xe2\\x99\\xaf73': 37, 'B3': 38,
    'C4': 39, 'C\\xe2\\x99\\xaf74': 40, 'D4': 41, 'D\\xe2\\x99\\xaf74': 42, 'E4': 43, 'F4': 44, 'F\\xe2\\x99\\xaf74': 45, 'G4': 46, 'G\\xe2\\x99\\xaf74': 47, 'A4': 48, 'A\\xe2\\x99\\xaf74': 49, 'B4': 50,
    'C5': 51, 'C\\xe2\\x99\\xaf75': 52, 'D5': 53, 'D\\xe2\\x99\\xaf75': 54, 'E5': 55, 'F5': 56, 'F\\xe2\\x99\\xaf75': 57, 'G5': 58, 'G\\xe2\\x99\\xaf75': 59, 'A5': 60, 'A\\xe2\\x99\\xaf75': 61, 'B5': 62,
    'C6': 63, 'C\\xe2\\x99\\xaf76': 64, 'D6': 65, 'D\\xe2\\x99\\xaf76': 66, 'E6': 67, 'F6': 68, 'F\\xe2\\x99\\xaf76': 69, 'G6': 70, 'G\\xe2\\x99\\xaf76': 71, 'A6': 72, 'A\\xe2\\x99\\xaf76': 73, 'B6': 74,
    'C7': 75, 'C\\xe2\\x99\\xaf77': 76, 'D7': 77, 'D\\xe2\\x99\\xaf77': 78, 'E7': 79, 'F7': 80, 'F\\xe2\\x99\\xaf77': 81, 'G7': 82, 'G\\xe2\\x99\\xaf77': 83, 'A7': 84, 'A\\xe2\\x99\\xaf77': 85, 'B7': 86,
    'C8': 87
}

def colorWipeAll(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)


def setColorByIndices(strip, indices, color=Color(0, 128, 0), wait_ms=50):
    for index in indices:
        if index < 0 or index >= strip.numPixels():
            continue
        strip.setPixelColor(index, color)
        
    strip.show()
    time.sleep(wait_ms/1000.0)

def on_connect(client, userdata, flags, rc):
    print("Connection returned result: "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("your_topic", qos=1)
    
# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected Disconnect')
    else:
        print('Expected Disconnect')

# The default message callback.
# (you can create separate callbacks per subscribed topic)
def on_message(client, userdata, message):
    
    # reset the strip
    setColorByIndices(strip, full_strip, Color(0,0,0), 10)
    input = str(message.payload.decode('utf-8'))
    print('Received message: "' + input + '" on topic "' + message.topic)

    # Split the input string into individual notes, strip spaces, and capitalize them
    notes = [note.strip().upper() for note in input.split()]

    # Optionally, print the list of notes for confirmation
    print("Current list of notes:", notes)
    
    setColorByIndices(strip, [note_to_led_index[note] for note in notes],wait_ms=200)

# Main program logic follows:
if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()
    
    # 1. create a client instance.
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # 2. connect to a broker using one of the connect*() functions.
    client.connect_async('test.mosquitto.org')
    # client.connect("mqtt.eclipse.org")

    # 3. call one of the loop*() functions to maintain network traffic flow with the broker.
    client.loop_start()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    
    full_strip = [i for i in range(strip.numPixels())]

    print ('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    try:

        print ('INITIALIZING: Color wipe animations.')
        colorWipeAll(strip, Color(255, 0, 0))  # Red wipe
        colorWipeAll(strip, Color(0, 255, 0))  # Blue wipe
        colorWipeAll(strip, Color(0, 0, 255))  # Green wipe
        colorWipeAll(strip, Color(0,0,0), 10)
        print('Ready...')
            
        while True:
            pass

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()
        if args.clear:
            colorWipeAll(strip, Color(0,0,0), 10)