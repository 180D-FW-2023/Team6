from rpi_ws281x import *
from datetime import datetime, timedelta
import time

# LED strip configuration:
LED_COUNT      = 15     # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating a signal (try 10)
LED_BRIGHTNESS = 25      # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

################ LED CODE #####################

recently_on = {i:None for i in range(87)}
offset = 27

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
# Intialize the library (must be called once before other functions).
strip.begin()

note_to_led_index = {
    'A0': 0, 'A♯0': 1, 'B0': 2,
    'C1': 3, 'C♯1': 4, 'D1': 5, 'D♯1': 6, 'E1': 7, 'F1': 8, 'F♯1': 9, 'G1': 10, 'G♯1': 11, 'A1': 12, 'A♯1': 13, 'B1': 14,
    'C2': 15, 'C♯2': 16, 'D2': 17, 'D♯2': 18, 'E2': 19, 'F2': 20, 'F♯2': 21, 'G2': 22, 'G♯2': 23, 'A2': 24, 'A♯2': 25, 'B2': 26,
    'C3': 27, 'C♯3': 28, 'D3': 29, 'D♯3': 30, 'E3': 31, 'F3': 32, 'F♯3': 33, 'G3': 34, 'G♯3': 35, 'A3': 36, 'A♯3': 37, 'B3': 38,
    'C4': 39, 'C♯4': 40, 'D4': 41, 'D♯4': 42, 'E4': 43, 'F4': 44, 'F♯4': 45, 'G4': 46, 'G♯4': 47, 'A4': 48, 'A♯4': 49, 'B4': 50,
    'C5': 51, 'C♯5': 52, 'D5': 53, 'D♯5': 54, 'E5': 55, 'F5': 56, 'F♯5': 57, 'G5': 58, 'G♯5': 59, 'A5': 60, 'A♯5': 61, 'B5': 62,
    'C6': 63, 'C♯6': 64, 'D6': 65, 'D♯6': 66, 'E6': 67, 'F6': 68, 'F♯6': 69, 'G6': 70, 'G♯6': 71, 'A6': 72, 'A♯6': 73, 'B6': 74,
    'C7': 75, 'C♯7': 76, 'D7': 77, 'D♯7': 78, 'E7': 79, 'F7': 80, 'F♯7': 81, 'G7': 82, 'G♯7': 83, 'A7': 84, 'A♯7': 85, 'B7': 86,
    'C8': 87,
    'A0': 0, 'A#0': 1, 'B0': 2,
    'C1': 3, 'C#1': 4, 'D1': 5, 'D#1': 6, 'E1': 7, 'F1': 8, 'F#1': 9, 'G1': 10, 'G#1': 11, 'A1': 12, 'A#1': 13, 'B1': 14,
    'C2': 15, 'C#2': 16, 'D2': 17, 'D#2': 18, 'E2': 19, 'F2': 20, 'F#2': 21, 'G2': 22, 'G#2': 23, 'A2': 24, 'A#2': 25, 'B2': 26,
    'C3': 27, 'C#3': 28, 'D3': 29, 'D#3': 30, 'E3': 31, 'F3': 32, 'F#3': 33, 'G3': 34, 'G#3': 35, 'A3': 36, 'A#3': 37, 'B3': 38,
    'C4': 39, 'C#4': 40, 'D4': 41, 'D#4': 42, 'E4': 43, 'F4': 44, 'F#4': 45, 'G4': 46, 'G#4': 47, 'A4': 48, 'A#4': 49, 'B4': 50,
    'C5': 51, 'C#5': 52, 'D5': 53, 'D#5': 54, 'E5': 55, 'F5': 56, 'F#5': 57, 'G5': 58, 'G#5': 59, 'A5': 60, 'A#5': 61, 'B5': 62,
    'C6': 63, 'C#6': 64, 'D6': 65, 'D#6': 66, 'E6': 67, 'F6': 68, 'F#6': 69, 'G6': 70, 'G#6': 71, 'A6': 72, 'A#6': 73, 'B6': 74,
    'C7': 75, 'C#7': 76, 'D7': 77, 'D#7': 78, 'E7': 79, 'F7': 80, 'F#7': 81, 'G7': 82, 'G#7': 83, 'A7': 84, 'A#7': 85, 'B7': 86,
    'C8': 87
}

def start_sequence():
    rainbow(wait_ms=20, iterations=1)
    colorWipeAll(wait_ms=50)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def colorWipeAll(color=Color(0,0,0), wait_ms=50):
    """ Wipe color across display a pixel at a time. """
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)


def showOneColorOnly(index, color=Color(128, 128, 128), wait_ms=50):
    print("Received index: ", index)
    if not (index < offset or index >= LED_COUNT+offset):
        print("Setting Pixel: ", index-offset)
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0,0,0))
        strip.setPixelColor(index-offset, color)
    strip.show()
    
def setColorByIndex(index, color=(0,128,0)):
    if not (index < offset or index >= LED_COUNT+offset):
        strip.setPixelColor(index-offset, color)
    strip.show()

def multiColor(indices, color = Color(128, 128, 128)):
    now = datetime.now()
    print("setting multicolor")
    for index in indices:
        print('poop: ', index)
        if not (index < offset or index >= LED_COUNT+offset):
            strip.setPixelColor(index-offset, color)
            recently_on[index] = now
    
    strip.show()
            
def turnOffExpired(on_time=0.25):
    now = datetime.now()
    off_color = Color(0,0,0)
    
    for key, timestamp in recently_on.items():
        if timestamp and now - timestamp > timedelta(seconds=on_time):     # if the LED has been on for more than 0.5 seconds
            recently_on[key] = None
            strip.setPixelColor(key-offset, off_color)
    
    strip.show()
    
def testModeCheckDup(note, time_diff=1):
    now = datetime.now()
    
    if not recently_on[note_to_led_index[note]]:
        # hasnt been played recently
        recently_on[note_to_led_index[note]] = now
        return False
    
    if recently_on[note_to_led_index[note]] and now - recently_on[note_to_led_index[note]] > timedelta(seconds=time_diff):
        # played but timed out
        recently_on[note_to_led_index[note]] = now
        return False
    
    # played and havent timed out
    return True
        
    

        