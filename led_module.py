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

index_to_note = {
    6: 'G♯4',
    7: 'G4',
    8: 'F♯4',
    9: 'F4',
    10: 'E4',
    11: 'D♯4',
    12: 'D4',
    13: 'C♯4',
    14: 'C4',
    15: 'B3',
    16: 'A♯3',
    17: 'A3',
    18: 'G♯3',
    19: 'G3',
    20: 'F♯3',
    21: 'F3',
    22: 'E3',
    23: 'D♯3',
    24: 'D3',
    25: 'C♯3',
    26: 'C3',
    27: 'B2',
    28: 'A♯2',
    29: 'A2'
}


def start_sequence():
    rainbow(wait_ms=20, iterations=1)
    colorWipeAll(wait_ms=10)

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
    
def setColorByIndices(indices, color=(0,128,0)):
    for index in indices:
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
            
def resetExpired(on_time=0.25, off_color=Color(0,0,0), indices = None):
    """
    Turn off expired notes.

    This function turns off LED notes that were recently played and have exceeded the specified on_time duration.
    If indices are specified, only the notes at the specified indices will be turned off.
    If indices are not specified, all expired notes will be turned off.

    Parameters:
    - on_time (float): The duration in seconds after which a note is considered expired. Default is 0.25 seconds, otherwise set lesson mode's on_time to 1.
    - off_color (Color): The color to set the LED to instead of turning it off. Default is Color(0,0,0).
    - indices (list): A list of indices specifying the notes to turn off. Default is None.

    Returns:
    None
    """
    
    now = datetime.now()
    
    if indices:
        for index in indices:
            if recently_on[index] and now - recently_on[index] > timedelta(seconds=on_time):
                recently_on[index] = None
                strip.setPixelColor(index-offset, off_color)
    else:
        # If indices not specified, turn off all expired notes
        for key, timestamp in recently_on.items():
            if timestamp and now - timestamp > timedelta(seconds=on_time):
                recently_on[key] = None
                strip.setPixelColor(key-offset, off_color)
    strip.show()
    
def getNotesWithinInterval(time_interval=1):
    global recently_on
    now = datetime.now()

    # Filter out notes not within the TIME_INTERVAL
    valid_notes = [index_to_note[note] for note, timing in recently_on.items() if timing is not None and now - timing <= timedelta(seconds=time_interval)]

    return valid_notes
    
def testModeCheckDup(index, time_diff=1):
    now = datetime.now()
    
    if not recently_on[index]:
        # hasnt been played recently
        recently_on[index] = now
        return False
    
    if recently_on[index] and now - recently_on[index] > timedelta(seconds=time_diff):
        # played but timed out
        recently_on[index] = now
        return False
    
    # played and havent timed out
    return True
        
    

        