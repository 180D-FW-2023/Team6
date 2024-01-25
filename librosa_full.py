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
seconds = 0.05 # Duration of recording
record = 1 #whether or not to record
i = 0
prev_l = ""
onsets = np.array([])
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
    

    '''
    fig, ax = plt.subplots()

    img = librosa.display.specshow(librosa.amplitude_to_db(newS,ref=np.max),y_axis='log', x_axis='time', ax=ax)

    ax.set_title('Power spectrogram')

    fig.colorbar(img, ax=ax, format="%+2.0f dB")

    ax.set_title('Power spectrogram')

    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    plt.show()
    '''
    
        #print("loop")
        #print(p)
    print("max_noise" + str(max_noise))
    #print(first_or_None)
    if max_noise < 100:
        l = ""
    print(l)
    #m = l + " " + str(i)
    #print(m)
    client.publish('your_topic', l, qos=1)

    #get onset of notes and calculate tempo
    cur_onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    if l != prev_l:
        np.append(onsets, i * seconds)
    np.append(onsets, cur_onsets)
    #tempo = 60 / (onsets[-1] - onsets[-2])
    #client.publish('your_topic', tempo, qos=1)
    
    prev_l = l
    i = i + 1

client.loop_stop()
client.disconnect()
