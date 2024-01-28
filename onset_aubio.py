import aubio
import numpy as np
import sounddevice as sd

def onset_detection_callback(frame, time, status):
    onset = onset_detector(frame)
    if onset:
        print("Onset detected!")

# Set up audio input parameters
sample_rate = 44100
channels = 1  # Change to 2 if using stereo input
buffer_size = 1024

# Initialize the onset detector
onset_detector = aubio.onset("default", buffer_size, 1, sample_rate)

# Set up the input stream using sounddevice
stream = sd.InputStream(callback=onset_detection_callback,
                       channels=channels,
                       samplerate=sample_rate,
                       blocksize=buffer_size)

# Start the stream
stream.start()

# Keep the script running to capture real-time audio input
try:
    print("Press Ctrl+C to exit.")
    sd.wait()
except KeyboardInterrupt:
    print("Exiting...")

# Stop the stream
stream.stop()
stream.close()