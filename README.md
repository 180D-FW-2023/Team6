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

# Camera
scikit-learn
cv2

# Misc
scipy
matplotlib
numpy
paho-mqtt
pickle
threading
```

# Running the code
Use `start.sh` to run the code. This will:
1. Create the named pipe
2. Run the audio processing script
3. Run the CV + LED processing script


# Methodology

![Workflow](/images/workflow.png)

