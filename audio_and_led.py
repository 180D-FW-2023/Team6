#import libraries
import sounddevice as sd
from scipy.io.wavfile import write
from scipy.io import wavfile
import librosa

from collections import OrderedDict
import matplotlib.pyplot as plt
import numpy as np
np.set_printoptions(threshold=np.inf)

import time
from rpi_ws281x import *
import paho.mqtt.client as mqtt

# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.

# LED strip configuration:
LED_COUNT      = 15     # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating a signal (try 10)
LED_BRIGHTNESS = 65      # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

################ LED CODE #####################

full_strip = [i for i in range(LED_COUNT)]

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
    'C8': 87
}

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

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def colorWipeAll(strip, color, wait_ms=50):
    """ Wipe color across display a pixel at a time. """
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)


def setColorByIndices(strip, index, color=Color(0, 128, 0), wait_ms=50):
    """ Sets pixel at indices then show all changes at once """
    print("Received index: ", index)
    if not (index < 30 or index >= strip.numPixels()+30):
        print("Setting Pixel: ", index-30)
        for i in range(15):
            strip.setPixelColor(i, Color(0,0,0))

        print("Turned off everything else")
        strip.setPixelColor(index-30, color)
    strip.show()

################ LIBROSA SETUP #####################

fs = 32000  # Sample rate
seconds = 0.1 # Duration of recording
record = 1 #whether or not to record
i = 0
prev_l = ""
onsets = np.array([])
target_notes = []
# target_notes = ['E3', 'F♯3', 'G♯3', 'A3', 'B3', 'C♯4', 'D♯4', 'E4']
played_notes = []

################## MQTT SETUP #####################

# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connection returned result: "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("scale_lesson")

# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected Disconnect')
    else:
        print('Expected Disconnect')

def on_message(client, userdata, message):
    # topic = msg.topic
    # print("topic: ",topic)
    # m_decode=str(msg.payload.decode("utf-8","ignore"))
    # # print("data Received type",type(m_decode))
    # # print("data Received",m_decode)
    # # print("Converting from Json to Object")
    # m_in = json.loads(m_decode) #decode json data
    # print(type(m_in))
    # print("Command = ",m_in["command"])
    # if m_in["command"] == "scale":
    #     target_notes = m_in["notes"]
    #     print(notes)
    #     setColorByIndices(strip, target_notes[0], color=Color(0,0,128),wait_ms=50)
    
    # color sequence to indicate that a new training has been received
    colorWipeAll(strip, Color(128,0,0), wait_ms=50)
    colorWipeAll(strip, Color(0,128,0), wait_ms=50)
    colorWipeAll(strip, Color(0,0,128), wait_ms=50)
    
    topic = str(message.topic)
    scale = str(message.payload.decode("utf-8","ignore"))
    print('Received message: "' + str(message.payload) + '" on topic "' +
            message.topic + '" with QoS ' + str(message.qos))
    
    if topic == "scale_lesson":
        target_notes = scale.split()
        played_notes = []
        print(target_notes)
        # set first color to blue
        setColorByIndices(strip, target_notes[0], color=Color(0,0,128),wait_ms=50)
    
# 1. create a client instance.
client = mqtt.Client()

# add additional client options (security, certifications, etc.)
# many default options should be good to start off.
# add callbacks to client.
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# 2. connect to a broker using one of the connect*() functions.
client.connect_async('test.mosquitto.org')
client.loop_start()


################## MAIN LOOP #####################

print("Initializing LED strip")
rainbow(strip, wait_ms=20, iterations=1)
colorWipeAll(strip, Color(0,0,0), wait_ms=50)


while True:
    #record audio buffer
    if (record == 1):
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        sd.wait()  # Wait until recording is finished
        write('output.wav', fs, myrecording)  # Save as WAV file 


    sr, data = wavfile.read('output.wav')

    #filter audio buffer

    y = np.asarray(data).astype(float)
    
    max_noise = np.max(np.abs(librosa.stft(y)))
    oldD = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    mask = (oldD[:, -10:-1] > -21).all(1)
    blank = -80
    newD = np.full_like(oldD, blank)
    newD[mask] = oldD[mask]
    newS=librosa.db_to_amplitude(newD)

    #get pitches from filtered audio
    pitches, magnitudes = librosa.piptrack(S=newS, sr=sr)
    pitches_final = pitches[np.asarray(magnitudes > 0.12).nonzero()]
    if len(pitches_final) > 0:
        notes = librosa.hz_to_note(pitches_final)
        notes = list(OrderedDict.fromkeys(notes))
    else:
        notes = ""
    
    l = " ".join(notes)
    first_or_None = ""
    if len(notes) > 0:
        first_or_None = notes[0]
    else:
        first_or_None = ""
    
    
    #print(first_or_None)
    if max_noise < 100:
        l = ""
    print(l)
    
    prev_l = l

    notes = [note.strip().upper() for note in l.split()]
    top_note = notes[0] if notes else None

    if top_note:
        print("Curr Note: ", top_note)
        
        if target_notes and len(played_notes) < len(target_notes):
            if top_note == target_notes[len(played_notes)]:
                print("Correct!")
                setColorByIndices(strip, note_to_led_index[top_note], color=Color(0,128,0),wait_ms=500)
            else:
                print("Wrong!")
                setColorByIndices(strip, note_to_led_index[top_note], color=Color(128,0,0),wait_ms=500)
            
            played_notes.append(notes[0])
            
            if len(played_notes) == len(target_notes):
                print("Finished!")
                rainbow(strip, wait_ms=20, iterations=1)
                # reset everything
                colorWipeAll(strip, Color(0,0,0), wait_ms=50)
                played_notes = []
                target_notes = []
            else:
                # sets next note to blue
                setColorByIndices(strip, target_notes[len(played_notes)], color=Color(0,0,128),wait_ms=50)
            
        else:
            # default note playing - shows white light
            print("Default")
            setColorByIndices(strip, note_to_led_index[top_note], color=Color(128,128,128),wait_ms=200)

