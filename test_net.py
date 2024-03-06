import numpy as np
import tensorflow as tf

import sounddevice as sd
from scipy.io.wavfile import write
import librosa
import matplotlib.pyplot as plt
import os
from PIL import Image
import keras.utils as image

SAMPLE_RATE=44100
output_folder = "C:\Team6"

def record_audio(filename, duration, sample_rate):
    # Record audio
    recording = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()

    # Save the recorded audio to a WAV file
    write(filename, sample_rate, recording)

# Load TFLite model and allocate tensors.
interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
print(input_details)
output_details = interpreter.get_output_details()
print(output_details)

# Prepare your input data (modify according to your model's input requirements)
input_shape = input_details[0]['shape']

output_filename = "recorded_audio.wav"
recording_duration = 0.2  # in seconds

# Record audio and save to WAV file
record_audio(output_filename, recording_duration, 44100)

print(f"Audio recorded and saved as {output_filename}")

signal, samplerate = librosa.load(output_filename, sr=SAMPLE_RATE)

mel_spec = librosa.feature.melspectrogram(y=signal, sr=SAMPLE_RATE)
mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

plt.figure(figsize=(6, 4))
librosa.display.specshow(mel_spec_db, sr=SAMPLE_RATE, fmax=1024, x_axis='time', y_axis='mel')
#plt.colorbar(format='%+2.0f dB')
#plt.title('Mel Spectrogram')
plt.axis('off')
plt.show()
plt.savefig(os.path.join(output_folder, f"mel_spectrogram_chunk.png"), bbox_inches='tight', pad_inches=0)
plt.close()
img = image.load_img("C:\Team6\output_mel_spectrograms\mel_spectrogram_f_chunk_1250.png",target_size=(465,308,3))
img = image.load_img(os.path.join(output_folder, f"mel_spectrogram_chunk.png"),target_size=(465,308,3))
img = image.img_to_array(img)
img = img/255
img = np.expand_dims(img, axis=0)
# Set the input tensor
interpreter.set_tensor(input_details[0]['index'], img)

# Perform inference
interpreter.invoke()

# Get the output tensor
output_data = interpreter.get_tensor(output_details[0]['index'])

# Process the output (modify according to your model's output)
print("Output:", output_data)