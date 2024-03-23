# Team6

This is the directory for Team 6's Virtual Music Teacher code.


# Requirements

## Hardware
- A WS2812B LED Strip, or any LED strips compatible with `rpi_ws281x` library
- Raspberry Pi 4
- Logitech C920 Webcam
- A rig of some sort for the webcam, mounted overhead over piano keys
- A computer for the dashboard
- A piano (of course)

## Software
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
Use `start.sh` to run the code on the Raspberry Pi 4. This will:
1. Start the audio processing script
2. Start the CV script for detecting piano keypresses
3. Start the main controller for processing the note detection results and controlling the LED

# Code explanations and sources
## Audio
The `audio_writes_2.py` file contains the audio processing pipeline and integration into the larger project. 

The loop for handling the PyAudio buffer came from a demo for aubio pitch: https://github.com/aubio/aubio/blob/master/python/demos/demo_pyaudio.py.

The Harmonic Product Spectrum algorithm was taken from this GitHub repo: https://github.com/joaocarvalhoopen/Polyphonic_note_detector_using_Harmonic_Product_Spectrum.

HPS was selected to supplement Librosa due to its simplicity and speed.
The filtering on the spectrogram was minimal to improve detection of the correct note and reduce the rate of false negatives.

The number of bugs is hopefully zero; notes seem to be detected just fine in all scenarios tested, with no program crashing.

Future improvements include potentially using a different machine learning framework to efficiently read the audio buffer, or tweaking the manual spectrogram output to read peaks better without as many false positives while still keeping false negatives low.

## CV
The `cv_reads_2.py` file contains the CV processing pipeline and integration into the larger project. 


## LED
The `led_module.py` file contains the LED logic handling. Some of the code was taken from the `rpi_ws281x` library examples, and the rest was written by the team.

The `main_controller.py` file receives results from the audio, CV and dashboard and handles logic for the different playing modes then control the LED strip accordingly. While there isn't any bugs that will break the code, there may be some edge cases that will cause the LED strip to behave unexpectedly. For example, in the "Chord, Lesson Mode", if a user plays 2 out of the 3 notes, it should count as incomplete, turn the 2 notes RED for 0.5s, before resetting it back to BLUE. However, after turning RED, the LEDs for those notes will turn off instead, but the lesson can still operate as usual and nothing will crash.  Nonetheless, under most circumstances, the LED strip should work as intended. 

## Dashboard
See the `full_stack` folder. Frontend and backend scripts are in their respective folders. A README on how to develop on your own machine is present in the `frontend` folder.



# Methodology

![Workflow](/images/dashboard_flow.drawio.png)

