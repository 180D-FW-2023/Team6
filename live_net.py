#! /usr/bin/env python

# Use pyaudio to open the microphone and run aubio.pitch on the stream of
# incoming samples. If a filename is given as the first argument, it will
# record 5 seconds of audio to this location. Otherwise, the script will
# run until Ctrl+C is pressed.

# Examples:
#    $ ./python/demos/demo_pyaudio.py
#    $ ./python/demos/demo_pyaudio.py /tmp/recording.wav

import pyaudio
import sys
import numpy as np
import aubio
import librosa
from collections import OrderedDict
import math
import sounddevice as sd
import tensorflow as tf
from scipy.io.wavfile import write
import matplotlib.pyplot as plt
import os
from PIL import Image
import keras.utils as image

TWELVE_ROOT_OF_2 = math.pow(2, 1.0 / 12)
# initialise pyaudio
p = pyaudio.PyAudio()

FFT_SIZE = 4096
SAMPLE_RATE = 44100
# open stream
buffer_size = FFT_SIZE
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = SAMPLE_RATE
stream = p.open(format=pyaudio_format,
                channels=n_channels,
                rate=samplerate,
                input=True,
                frames_per_buffer=buffer_size)

if len(sys.argv) > 1:
    # record 5 seconds
    output_filename = sys.argv[1]
    record_duration = 5 # exit 1
    outputsink = aubio.sink(sys.argv[1], samplerate)
    total_frames = 0
else:
    # run forever
    outputsink = None
    record_duration = None

# setup pitch
tolerance = 0.8
win_s = FFT_SIZE # fft size
hop_s = buffer_size # hop size
#pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
#pitch_o.set_unit("midi")
#pitch_o.set_tolerance(tolerance)
o = aubio.onset("default", win_s, hop_s, samplerate)
onsets = []
max_buffer = [0]
buf_const = 2
fft_len = FFT_SIZE
output_folder = 'C:\Team6'

# Load TFLite model and allocate tensors.
interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("*** starting recording")
while True:
    try:
        audiobuffer = stream.read(buffer_size)
        signal = np.frombuffer(audiobuffer, dtype=np.float32)
        mel_spec = librosa.feature.melspectrogram(y=signal, sr=SAMPLE_RATE)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        plt.figure(figsize=(6, 4))
        librosa.display.specshow(mel_spec_db, sr=SAMPLE_RATE, fmax=1024, x_axis='time', y_axis='mel')
        #plt.colorbar(format='%+2.0f dB')
        #plt.title('Mel Spectrogram')
        plt.axis('off')
        plt.savefig(os.path.join(output_folder, f"mel_spectrogram_chunk.png"), bbox_inches='tight', pad_inches=0)
        plt.close()
        #input_data = Image.open(os.path.join(output_folder, f"mel_spectrogram_chunk.png"))
        img = image.load_img(os.path.join(output_folder, f"mel_spectrogram_chunk.png"),target_size=(465,308,3))
        img = image.img_to_array(img)
        img = img/255
        img = np.expand_dims(img, axis=0)
        interpreter.set_tensor(input_details[0]['index'], img)
        
        # Perform inference
        interpreter.invoke()
        
        # Get the output tensor
        output_data = interpreter.get_tensor(output_details[0]['index'])
        
        # Process the output (modify according to your model's output)
        print("Output:", output_data)
        # Map indices to class labels
        class_labels = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 
                        'C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 
                        'A#4', 'B4', 'C5']

        # Define a threshold
        threshold = 0.1

        # Get classes whose values are above the threshold
        classes_above_threshold = []
        for idx, value in enumerate(output_data[0]):
            if value > threshold:
                classes_above_threshold.append(class_labels[idx])

        # Print the classes
        print("Classes whose values are above", threshold)
        print(classes_above_threshold)           
                


        if outputsink:
            outputsink(signal, len(signal))

        if record_duration:
            total_frames += len(signal)
            if record_duration * samplerate < total_frames:
                break
    except KeyboardInterrupt:
        print("*** Ctrl+C pressed, exiting")
        break

print("*** done recording")
stream.stop_stream()
stream.close()
p.terminate()