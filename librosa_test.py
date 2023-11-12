import sounddevice as sd
from scipy.io.wavfile import write
import librosa
import numpy as np
np.set_printoptions(threshold=np.inf)
import matplotlib.pyplot as plt

fs = 44100  # Sample rate
seconds = 0.3 # Duration of recording


myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
sd.wait()  # Wait until recording is finished
write('output.wav', fs, myrecording)  # Save as WAV file 



y, sr = librosa.load('output.wav')
S = np.abs(librosa.stft(y))
pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
print(pitches[np.where(magnitudes>20)])
print(magnitudes[np.where(magnitudes>20)])


fig, ax = plt.subplots()

img = librosa.display.specshow(librosa.amplitude_to_db(S,ref=np.max),y_axis='log', x_axis='time', ax=ax)

ax.set_title('Power spectrogram')

fig.colorbar(img, ax=ax, format="%+2.0f dB")
plt.show()
