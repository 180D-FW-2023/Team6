import aubio
import numpy as np
import sys
import aubio
sample_rate = 44100 # use original source samplerate
hop_size = 512 # number of frames to read in one block


# Create the pitch detection object
pitch_detection = aubio.pitch()

# Replace "your_audio_file.wav" with the path to your audio file
filename = "recorded_audio.wav"
audio_file = aubio.source(filename, sample_rate, hop_size)

# Process the audio file and print the detected pitches
while True:
    samples, read = audio_file()
    pitch = pitch_detection(samples)[0]
    print(f"Pitch: {pitch:.2f} Hz")

    if read < hop_size:
        break

# Close the audio file
audio_file.close()
