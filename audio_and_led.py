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
import paho.mqtt.client as mqtt
import led_control as led
from rpi_ws281x import Color

'''
modes:
0 = default
1 = lesson
2 = test
'''

target_notes = []
played_notes = []
mode = 0 

################ LIBROSA SETUP #####################

fs = 32000  # Sample rate
seconds = 0.1 # Duration of recording
record = 1 #whether or not to record
prev_l = ""

################## MQTT SETUP #####################

# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connection returned result: "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("team6/lesson")
    client.subscribe("team6/test")

# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected Disconnect')
    else:
        print('Expected Disconnect')

def on_message(client, userdata, message):
    global target_notes, mode
    
    led.colorWipeAll(Color(128,0,0), wait_ms=50)
    led.colorWipeAll(Color(0,128,0), wait_ms=50)
    led.colorWipeAll(Color(0,0,128), wait_ms=50)
    led.colorWipeAll(Color(0,0,0), wait_ms=50)
    
    topic = str(message.topic)
    scale = str(message.payload.decode("utf-8","ignore"))
    print('Received message: "' + str(message.payload) + '" on topic "' +
            message.topic + '" with QoS ' + str(message.qos))
    
    target_notes = scale.split()
    played_notes = []
    print(target_notes)
    
    match topic:
        case "team6/lesson":
            mode = 1
            # set first color to blue
            led.setColorByIndices(strip, note_to_led_index_web[target_notes[0]], color=Color(0,0,128),wait_ms=50)
        case "team6/test":
            mode = 2
            
    
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
led.start_sequence()

def learn_mode(top_note):
    global mode, target_notes, played_notes
    pass
    # print("TARGET ", target_notes)
    # print("RECORDED ", played_notes)
    
    # if top_note == target_notes[len(played_notes)]:
    #     print("Correct!")
    #     led.setColorByIndices(led.note_to_led_index[top_note], color=Color(0,128,0),wait_ms=1000)
    #     led.setColorByIndices(led.note_to_led_index[top_note], color=Color(0,128,0),wait_ms=1000)
    # else:
    #     print("Wrong!")
    #     led.setColorByIndices(led.note_to_led_index[top_note], color=Color(128,0,0),wait_ms=1000)
    
    # played_notes.append(notes[0])
    
    # if len(played_notes) == len(target_notes):
    #     print("Finished!")
    #     mode = 0
    #     led.start_sequence()
    #     played_notes = []
    #     target_notes = []
    # else:
    #     # sets next note to blue
    #     led.setColorByIndices(led.note_to_led_index_web[target_notes[len(played_notes)]], color=Color(0,0,128),wait_ms=50)


def test_mode(top_note):
    global mode, target_notes, played_notes
    
    print("TARGET ", target_notes)
    print("RECORDED ", played_notes)
    
    if top_note == target_notes[len(played_notes)]:
        print("Correct!")
        led.setColorByIndices(led.note_to_led_index[top_note], color=Color(0,128,0),wait_ms=1000)
        led.setColorByIndices(led.note_to_led_index[top_note], color=Color(0,128,0),wait_ms=1000)
    else:
        print("Wrong!")
        led.setColorByIndices(led.note_to_led_index[top_note], color=Color(128,0,0),wait_ms=1000)
    
    played_notes.append(notes[0])
    
    if len(played_notes) == len(target_notes):
        print("Finished!")
        mode = 0
        led.start_sequence()
        played_notes = []
        target_notes = []
    else:
        # sets next note to blue
        led.setColorByIndices(led.note_to_led_index_web[target_notes[len(played_notes)]], color=Color(0,0,128),wait_ms=50)


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
    
    prev_l = l

    notes = [note.strip().upper() for note in l.split()]
    top_note = notes[0] if notes else None

    if top_note:
        
        print("Curr Note: ", top_note)
        
        match mode:
            case 1:
                # lesson mode
                print("----- Lesson mode -----")
                lesson_mode(top_note)
            case 2:
                # test mode
                print("----- Test mode -----")
                test_mode(top_note)
            case _:
                # default note playing - shows white light
                print("----- Default mode -----")
                led.setColorByIndices(led.note_to_led_index[top_note], color=Color(128,128,128),wait_ms=200)

