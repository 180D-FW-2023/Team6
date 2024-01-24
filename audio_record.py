import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

fs = 22050  # Sample rate
seconds = 0.1 # Duration of recording

myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
sd.wait()  # Wait until recording is finished
write('test.wav', fs, myrecording)  # Save as WAV file 