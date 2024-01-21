from nnAudio import features
from scipy.io import wavfile
import torch
import librosa
import numpy as np
import matplotlib.pyplot as plt
sr, song = wavfile.read('test.wav') # Loading your audio
#x = song.mean(1) # Converting Stereo  to Mono
x = torch.tensor(song).float() # casting the array into a PyTorch Tensor

spec_layer = features.STFT(n_fft=2048, hop_length=512,
                              window='hann', freq_scale='log', pad_mode='reflect', sr=sr) # Initializing the model

spec = spec_layer(x) # Feed-forward your waveform to get the spectrogram
log_spec =np.array(spec)[0]# cast PyTorch Tensor back to numpy array
db_log_spec = librosa.amplitude_to_db(log_spec) # convert amplitude spec into db representation 
plt.figure()
img = librosa.display.specshow(db_log_spec,  y_axis='linear', x_axis='time', sr=sr)
plt.colorbar(img)