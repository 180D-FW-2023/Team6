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
import noisereduce as nr
import librosa
from collections import OrderedDict

# initialise pyaudio
p = pyaudio.PyAudio()

# open stream
buffer_size = 1024
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = 44100
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
win_s = 4096 # fft size
hop_s = buffer_size # hop size
pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(tolerance)
o = aubio.onset("default", win_s, hop_s, samplerate)
onsets = []
max_buffer = np.array([0])
buf_const = 10
print("*** starting recording")
while True:
    try:
        audiobuffer = stream.read(buffer_size)
        signal = np.frombuffer(audiobuffer, dtype=np.float32)
        #print(np.max(signal))
        #s = aubio.source(audiobuffer, samplerate, hop_s)
        filtered_signal = nr.reduce_noise(signal, samplerate, thresh_n_mult_nonstationary=2,stationary=False)
        thresh = np.sum(max_buffer[-buf_const:]) / len(max_buffer)
        max_buffer = np.append(max_buffer, np.max(signal))
        max_buffer = max_buffer[-buf_const:]

        '''
        These lines utilize aubio's pitch detection algorithm
        
        pitch = pitch_o(filtered_signal)[0]
        confidence = pitch_o.get_confidence()
        note = aubio.midi2note(int(pitch)+1)
        print("{} / {}".format(note,confidence))
        '''
        pitches, magnitudes = librosa.piptrack(S=np.abs(librosa.stft(filtered_signal)), sr=samplerate)
        #print(pitches[np.where(magnitudes>0)])
        #print(magnitudes[np.where(magnitudes>0)])
        pitches_final = pitches[np.asarray(magnitudes > 0.12).nonzero()]
        if len(pitches_final) > 0:
            notes = librosa.hz_to_note(pitches_final)
            notes = list(OrderedDict.fromkeys(notes))
        else:
            notes = ""
        #print(pitches_final)
        #print(notes)
        l = " ".join(notes)
        max_noise = np.max(np.abs(librosa.stft(filtered_signal)))
        print("max_noise" + str(max_noise))
        #print(first_or_None)
        if max_noise < 3:
            l = ""
        print(l)
        #samples, read = s()
        #if (np.max(filtered_signal) > np.sqrt(1.2) * thresh):
            #print("{} / {}".format(np.max(filtered_signal),thresh))
            
        if (max_noise > 3):
            if o(filtered_signal):
                print("%f" % o.get_last_s())
                onsets.append(o.get_last())

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