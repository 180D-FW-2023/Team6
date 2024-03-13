##!/bin/bash

python /home/pi/Team6/cv_reads_2.py &
python /home/pi/Team6/audio_writes_2.py &
sudo python /home/pi/Team6/main_controller.py &
wait
