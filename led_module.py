from rpi_ws281x import *
from datetime import datetime, timedelta
import time

# LED strip configuration:
LED_COUNT      = 35     # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating a signal (try 10)
LED_BRIGHTNESS = 5      # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

################ LED CODE #####################

recently_on = {i:None for i in range(30)}
offset = 0

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
# Intialize the library (must be called once before other functions).
strip.begin()

note_to_led_index = {
    'G#4': 6, 'G4': 7, 'F#4': 8, 'F4': 9, 'E4': 10, 'D#4': 11, 'D4': 12, 'C#4': 13, 'C4': 14,
    'B3': 15, 'A#3': 16, 'A3': 17, 'G#3': 18, 'G3': 19, 'F#3': 20, 'F3': 21, 'E3': 22, 'D#3': 23, 'D3': 24, 'C#3': 25, 'C3': 26,
    'B2': 27, 'A#2': 28, 'A2': 29
}

# The same applies for the sharps with the '♯' symbol.
note_to_led_index.update({
    'G♯4': 6, 'F♯4': 8, 'D♯4': 11, 'C♯4': 13,
    'A♯3': 16, 'G♯3': 18, 'F♯3': 20, 'D♯3': 23, 'C♯3': 25,
    'A♯2': 28
})

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

def colorWipeAll(color=Color(0,0,0), wait_ms=25):
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
    
def setRecentlyOn(index):
    now = datetime.now()
    recently_on[index] = now
    
def check_target_notes_within_interval(target_notes, time_interval=1):
    global recently_on
    now = datetime.now()

    # Filter out notes not within the TIME_INTERVAL
    valid_notes = [(note, timing) for note, timing in recently_on.items() if now - timing <= timedelta(seconds=time_interval)]

    # Check if there are exactly 3 target notes within the interval
    if len(valid_notes) == 3:
        played_notes = {note for note, _ in valid_notes}
        if set(played_notes) == set(target_notes) and len(played_notes) == len(target_notes):
            return True

    # If there are more than 3 notes or the notes don't match the target notes
    return False
    
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
        
    

        