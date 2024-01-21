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

fs = 44100  # Sample rate
seconds = 0.1 # Duration of recording
record = 0 #whether or not to record



sr, data = wavfile.read('test.wav')
#y, sr = librosa.load('output.wav',sr=None)
y = np.asarray(data).astype(float)
#print(y.shape)


#f0, voiced_flag, voiced_probs = librosa.pyin(y,fmin=librosa.note_to_hz('C2'),fmax=librosa.note_to_hz('C7'))
#times = librosa.times_like(f0)
max_noise = np.max(np.abs(librosa.stft(y)))
print(max_noise)
oldD = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
mask = (oldD[:, -5:-1] > -21).all(1)
blank = -80
newD = np.full_like(oldD, blank)
newD[mask] = oldD[mask]
newS=librosa.db_to_amplitude(newD)

pitches, magnitudes = librosa.piptrack(S=newS, sr=sr)
#print(pitches[np.where(magnitudes>0)])
#print(magnitudes[np.where(magnitudes>0)])
pitches_final = pitches[np.asarray(magnitudes > 0.15).nonzero()]
if len(pitches_final) > 0:
    notes = librosa.hz_to_note(pitches_final)
    notes = list(OrderedDict.fromkeys(notes))
else:
    notes = ""
print(pitches_final)
print(notes)
l = " ".join(notes)
print(l)

fig, ax = plt.subplots()

img = librosa.display.specshow(np.abs(librosa.stft(y)),y_axis='linear', x_axis='time', ax=ax)

ax.set_title('Power spectrogram')

fig.colorbar(img, ax=ax, format="%+2.0f dB")

ax.set_title('Power spectrogram')

fig.colorbar(img, ax=ax, format="%+2.0f dB")
plt.show()

fig, ax = plt.subplots()

img = librosa.display.specshow(librosa.amplitude_to_db(newS,ref=np.max),y_axis='log', x_axis='time', ax=ax)

ax.set_title('Power spectrogram')

fig.colorbar(img, ax=ax, format="%+2.0f dB")

ax.set_title('Power spectrogram')

fig.colorbar(img, ax=ax, format="%+2.0f dB")
plt.show()

    


