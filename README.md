# Team6

This is the directory for Team 6's code.


# Requirements

Use `pip install -r requirements.txt` to install all the necessary packages.
We advise using a Raspberry Pi 4 for better support.

Packages include:
```
# LED
rpi_ws281x==5.0.0
adafruit-circuitpython-neopixel
adafruit-blinka

# Audio
sounddevice
librosa
pyaudio
aubio

# Camera
scikit-learn
opencv-python
pupil-apriltags

# Misc
scipy
matplotlib
numpy
paho-mqtt
pickle
threading
zmq
```

# Running the code
Use `start.sh` to run the code. This will:
1. Create the named pipe
2. Run the audio processing script
3. Run the CV + LED processing script

# Code explanations and sources
## Audio
The `audio_writes_2.py' file contains the audio processing pipeline and integration into the larger project. 
The loop for handling the PyAudio buffer came from a demo for aubio pitch: `https://github.com/aubio/aubio/blob/master/python/demos/demo_pyaudio.py`.
The Harmonic Product Spectrum algorithm was tweaked based off this GitHub repo: `https://github.com/joaocarvalhoopen/Polyphonic_note_detector_using_Harmonic_Product_Spectrum`.
## CV
The `cv_reads_2.py' file contains the CV processing pipeline and integration into the larger project. 

## LED
The `led_module.py' file contains the LED logic handling.
The `main_controller.py` file receives results from the audio, CV and dashboard and handles control of the LED accordingly.

## Dashboard


# Methodology

![Workflow](/images/workflow.png)

