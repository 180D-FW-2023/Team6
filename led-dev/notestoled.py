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

full_strip = [i for i in range(LED_COUNT)]

note_to_led_index = {
    'A0': 0, 'A♯0': 1, 'B0': 2,
    'C1': 3, 'C♯1': 4, 'D1': 5, 'D♯1': 6, 'E1': 7, 'F1': 8, 'F♯1': 9, 'G1': 10, 'G♯1': 11, 'A1': 12, 'A♯1': 13, 'B1': 14,
    'C2': 15, 'C♯2': 16, 'D2': 17, 'D♯2': 18, 'E2': 19, 'F2': 20, 'F♯2': 21, 'G2': 22, 'G♯2': 23, 'A2': 24, 'A♯2': 25, 'B2': 26,
    'C3': 27, 'C♯3': 28, 'D3': 29, 'D♯3': 30, 'E3': 31, 'F3': 32, 'F♯3': 33, 'G3': 34, 'G♯3': 35, 'A3': 36, 'A♯3': 37, 'B3': 38,
    'C4': 39, 'C♯4': 40, 'D4': 41, 'D♯4': 42, 'E4': 43, 'F4': 44, 'F♯4': 45, 'G4': 46, 'G♯4': 47, 'A4': 48, 'A♯4': 49, 'B4': 50,
    'C5': 51, 'C♯5': 52, 'D5': 53, 'D♯5': 54, 'E5': 55, 'F5': 56, 'F♯5': 57, 'G5': 58, 'G♯5': 59, 'A5': 60, 'A♯5': 61, 'B5': 62,
    'C6': 63, 'C♯6': 64, 'D6': 65, 'D♯6': 66, 'E6': 67, 'F6': 68, 'F♯6': 69, 'G6': 70, 'G♯6': 71, 'A6': 72, 'A♯6': 73, 'B6': 74,
    'C7': 75, 'C♯7': 76, 'D7': 77, 'D♯7': 78, 'E7': 79, 'F7': 80, 'F♯7': 81, 'G7': 82, 'G♯7': 83, 'A7': 84, 'A♯7': 85, 'B7': 86,
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
        if index < 30 or index >= strip.numPixels()+30:
            continue
        strip.setPixelColor(index-30, color)
        
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
    colorWipeAll(strip, Color(0,0,0), 10)
    # setColorByIndices(strip, full_strip, Color(0,0,0), 200)
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

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    
    

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
        
        # 3. call one of the loop*() functions to maintain network traffic flow with the broker.
        client.loop_start()
        
        while True:
            pass

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()
        if args.clear:
            colorWipeAll(strip, Color(0,0,0), 10)