##!/bin/bash

python /home/pi/Team6/cv_writes.py &
python /home/pi/Team6/audio_reads.py &
sudo python /home/pi/Team6/main_controller.py &
wait
