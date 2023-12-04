import time
from rpi_ws281x import *
import argparse
import sys

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

def frequency_to_note(frequency):
    # Constants for the formula
    A4 = 440
    A4_INDEX = 49

    # Calculate the number of half steps away from A4
    n = round(12 * math.log2(frequency/A4)) + A4_INDEX

    return n

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

# Main program logic:
if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Initialize the library (must be called once before other functions).
    strip.begin()

    print('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    try:
        while True:
            # Read from stdin
            input_line = sys.stdin.readline().strip()
            if input_line:
                # Process the input and update LEDs
                input_line = input_line.strip()
                frequency_to_note(input_line)

    except KeyboardInterrupt:
        if args.clear:
            colorWipeAll(strip, Color(0,0,0), 10)