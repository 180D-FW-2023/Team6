#import libraries
import sounddevice as sd
from scipy.io.wavfile import write
from scipy.io import wavfile
import librosa
import numpy as np
from collections import OrderedDict
np.set_printoptions(threshold=np.inf)
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import numpy as np

import time
from rpi_ws281x import *
import argparse
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

def colorWipeAll(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)


def setColorByIndices(strip, index, color=Color(0, 128, 0), wait_ms=50):
    print("Received index: ", index)
    if not (index < 30 or index >= strip.numPixels()+30):
        print("Setting Pixel: ", index-30)
        for i in range(15):
            strip.setPixelColor(i, Color(0,0,0))

        print("Turned off everything else")
        strip.setPixelColor(index-30, color)
    strip.show()
fs = 32000  # Sample rate
seconds = 0.1 # Duration of recording
record = 1 #whether or not to record
i = 0
prev_l = ""
onsets = np.array([])

colorWipeAll(strip, Color(255, 0, 0))
while True:
    #record audio buffer
    if (record == 1):
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        sd.wait()  # Wait until recording is finished
        write('output.wav', fs, myrecording)  # Save as WAV file 


    sr, data = wavfile.read('output.wav')

    #filter audio buffer

    #y, sr = librosa.load('output.wav',sr=None)
    y = np.asarray(data).astype(float)
    #print(y.shape)
    
    max_noise = np.max(np.abs(librosa.stft(y)))
    #f0, voiced_flag, voiced_probs = librosa.pyin(y,fmin=librosa.note_to_hz('C2'),fmax=librosa.note_to_hz('C7'))
    #times = librosa.times_like(f0)
    oldD = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    mask = (oldD[:, -10:-1] > -21).all(1)
    blank = -80
    newD = np.full_like(oldD, blank)
    newD[mask] = oldD[mask]
    newS=librosa.db_to_amplitude(newD)

    #get pitches from filtered audio
    pitches, magnitudes = librosa.piptrack(S=newS, sr=sr)
    #print(pitches[np.where(magnitudes>0)])
    #print(magnitudes[np.where(magnitudes>0)])
    pitches_final = pitches[np.asarray(magnitudes > 0.12).nonzero()]
    if len(pitches_final) > 0:
        notes = librosa.hz_to_note(pitches_final)
        notes = list(OrderedDict.fromkeys(notes))
    else:
        notes = ""
    #print(pitches_final)
    #print(notes)
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

    # print(notes)
    print("Curr Note: ", notes[0] if notes else None)

    if notes:
        setColorByIndices(strip, note_to_led_index[notes[0]],wait_ms=200)


    i = i + 1








# # The default message callback.
# # (you can create separate callbacks per subscribed topic)
# def on_message(client, userdata, message):
    
#     # reset the strip
#     colorWipeAll(strip, Color(0,0,0), 10)
#     # setColorByIndices(strip, full_strip, Color(0,0,0), 200)
#     input = str(message.payload.decode('utf-8'))
#     print('Received message: "' + input + '" on topic "' + message.topic)

#     # Split the input string into individual notes, strip spaces, and capitalize them
#     notes = [note.strip().upper() for note in input.split()]

#     # Optionally, print the list of notes for confirmation
#     print("Current list of notes:", notes)
    
#     setColorByIndices(strip, [note_to_led_index[note] for note in notes],wait_ms=200)

#     # Create NeoPixel object with appropriate configuration.
#     strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
#     # Intialize the library (must be called once before other functions).
#     strip.begin()
    

    # try:

    #     print ('INITIALIZING: Color wipe animations.')
    #     colorWipeAll(strip, Color(255, 0, 0))  # Red wipe
    #     colorWipeAll(strip, Color(0, 255, 0))  # Blue wipe
    #     colorWipeAll(strip, Color(0, 0, 255))  # Green wipe
    #     colorWipeAll(strip, Color(0,0,0), 10)
    #     print('Ready...')
        
        
    #     while True:
    #         pass

    # except KeyboardInterrupt:
    #     colorWipeAll(strip, Color(0,0,0), 10)

