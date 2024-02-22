##!/bin/bash

python3 /home/pi/cv_writes.py &
python3 /home/pi/audio_reads.py &
sudo python3 /home/pi/main_controller.py &
wait
