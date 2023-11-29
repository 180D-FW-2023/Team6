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

fs = 32000  # Sample rate
seconds = 0.2 # Duration of recording
record = 1 #whether or not to record
i = 0
while True:
    if (record == 1):
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        sd.wait()  # Wait until recording is finished
        write('output.wav', fs, myrecording)  # Save as WAV file 


    sr, data = wavfile.read('output.wav')
    #y, sr = librosa.load('output.wav',sr=None)
    y = np.asarray(data).astype(float)
    #print(y.shape)
    S = np.abs(librosa.stft(y))

    #f0, voiced_flag, voiced_probs = librosa.pyin(y,fmin=librosa.note_to_hz('C2'),fmax=librosa.note_to_hz('C7'))
    #times = librosa.times_like(f0)
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    mask = (D[:, -3:-1] > -26).all(1)
    blank = -80
    newD = np.full_like(D, blank)
    newD[mask] = D[mask]
    newS=librosa.db_to_amplitude(newD)
    '''
    fig, ax = plt.subplots()

    img = librosa.display.specshow(librosa.amplitude_to_db(newS,ref=np.max),y_axis='log', x_axis='time', ax=ax)

    ax.set_title('Power spectrogram')

    fig.colorbar(img, ax=ax, format="%+2.0f dB")

    ax.set_title('Power spectrogram')

    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    plt.show()
    '''
    pitches, magnitudes = librosa.piptrack(S=newS, sr=sr)
    #print(pitches[np.where(magnitudes>0)])
    #print(magnitudes[np.where(magnitudes>0)])
    pitches_final = pitches[np.asarray(magnitudes > 0.12).nonzero()]
    if len(pitches_final) > 0:
        notes = librosa.hz_to_note(pitches_final)
        notes = list(OrderedDict.fromkeys(notes))
    else:
        notes = ""
    print(pitches_final)
    print(notes)

        #print("loop")
        #print(p)
    client.publish('ece180d/test', str(notes), qos=1)
    i = i + 1

client.loop_stop()
client.disconnect()
