import sounddevice as sd
from scipy.io.wavfile import write
import librosa
import numpy as np
np.set_printoptions(threshold=np.inf)
import matplotlib.pyplot as plt

fs = 44100  # Sample rate
seconds = 0.3 # Duration of recording
record = 0 #whether or not to record

if (record == 1):
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait until recording is finished
    write('output.wav', fs, myrecording)  # Save as WAV file 



y, sr = librosa.load('output.wav')
S = np.abs(librosa.stft(y))

f0, voiced_flag, voiced_probs = librosa.pyin(y,fmin=librosa.note_to_hz('C2'),fmax=librosa.note_to_hz('C7'))
times = librosa.times_like(f0)
D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
mask = (D[:, 11:] > -29).all(1)
blank = -80
newD = np.full_like(D, blank)
newD[mask] = D[mask]
newS=librosa.db_to_amplitude(newD)

pitches, magnitudes = librosa.piptrack(S=newS, sr=sr)
print(pitches[np.where(magnitudes>0)])
print(magnitudes[np.where(magnitudes>0)])
print(librosa.hz_to_note(pitches[np.where(magnitudes>0)]))


fig, ax = plt.subplots()
img = librosa.display.specshow(newD, x_axis='time', y_axis='log', ax=ax)
ax.set(title='pYIN fundamental frequency estimation')
fig.colorbar(img, ax=ax, format="%+2.f dB")
ax.plot(times, f0, label='f0', color='cyan', linewidth=3)
ax.legend(loc='upper right')
#img = librosa.display.specshow(S,y_axis='fft', x_axis='time', ax=ax)

ax.set_title('Power spectrogram')

fig.colorbar(img, ax=ax, format="%+2.0f dB")
plt.show()
