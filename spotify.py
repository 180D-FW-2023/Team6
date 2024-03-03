import tensorflow as tf

from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
import sounddevice as sd
from scipy.io.wavfile import write

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
TWELVE_ROOT_OF_2 = math.pow(2, 1.0 / 12)
# initialise pyaudio
p = pyaudio.PyAudio()

FFT_SIZE = 4096
SAMPLE_RATE = 22050
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
pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(tolerance)
o = aubio.onset("default", win_s, hop_s, samplerate)
onsets = []
max_buffer = [0]
buf_const = 2
fft_len = FFT_SIZE

basic_pitch_model = tf.saved_model.load(str(ICASSP_2022_MODEL_PATH))

print("*** starting recording")
while True:
    try:
        audiobuffer = stream.read(buffer_size)
        signal = np.frombuffer(audiobuffer, dtype=np.float32)
        write("recorded_audio.wav", samplerate, signal)

        model_output, midi_data, note_events = predict(
        "recorded_audio.wav",
        basic_pitch_model,
        )
        #print(note_events)
        third_items = [row[2] for row in note_events]
        print(third_items)
        notes = []
        for i in third_items:
            notes.append(librosa.midi_to_note(i))
        print(notes)
    except KeyboardInterrupt:
        print("*** Ctrl+C pressed, exiting")
        break

print("*** done recording")
stream.stop_stream()
stream.close()
p.terminate()

