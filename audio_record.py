import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

fs = 44100  # Sample rate
seconds = 0.3 # Duration of recording

myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype=np.int16)
sd.wait()  # Wait until recording is finished
write('test.wav', fs, myrecording)  # Save as WAV file 