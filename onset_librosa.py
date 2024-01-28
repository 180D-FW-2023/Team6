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
# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connection returned result: "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("ece180d/test")
# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected Disconnect')
    else:
     print('Expected Disconnect')
# The default message callback.
# (won’t be used if only publishing, but can still exist)
def on_message(client, userdata, message):
    print('Received message: "' + str(message.payload) + '" on topic "' +
        message.topic + '" with QoS ' + str(message.qos))
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
# 3. call one of the loop*() functions to maintain network traffic flow with the broker.
client.loop_start()
# 4. use subscribe() to subscribe to a topic and receive messages.
# 5. use publish() to publish messages to the broker.
# payload must be a string, bytearray, int, float or None.


# 6. use disconnect() to disconnect from the broker.

fs = 44100  # Sample rate
seconds = 0.1 # Duration of recording
record = 1 #whether or not to record
i = 0

onsets = np.array([])
while True:
    #record audio buffer
    if (record == 1):
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        sd.wait()  # Wait until recording is finished
        write('output.wav', fs, myrecording)  # Save as WAV file 


    sr, data = wavfile.read('output.wav')

    #strength
    ye, sre = librosa.load('test.wav')
    onset_env = librosa.onset.onset_strength(y=ye, sr=sre)
    #filter audio buffer

    #y, sr = librosa.load('output.wav',sr=None)
    y = np.asarray(data).astype(float)

    #get onset of notes and calculate tempo
    cur_onsets = librosa.onset.onset_detect(y=y, onset_envelope=onset_env, fwsr=sr, units='time')
    print(cur_onsets)
    if (cur_onsets.size>0):
        detected = True
    else:
        detected = False
    print(detected)
    np.append(onsets, i * seconds + cur_onsets)
    #np.append(onsets, cur_onsets)
    #tempo = 60 / (onsets[-1] - onsets[-2])
    client.publish('your_topic', detected, qos=1)
    print(onsets)
    i = i + 1

client.loop_stop()
client.disconnect()
