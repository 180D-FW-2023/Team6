#!/bin/bash

# Define the named pipe's path
PIPE_PATH="./audio_output"

# Function to clean up the named pipe on exit
cleanup() {
    echo "Cleaning up..."
    rm -f "$PIPE_PATH"
    exit
}

# Trap signals for cleanup
trap cleanup SIGINT SIGTERM

# Create the named pipe if it doesn't already exist
if [[ ! -p $PIPE_PATH ]]; then
    mkfifo "$PIPE_PATH"
fi

# Run your scripts in the background
# Assuming Python 3.x is the executable for Python scripts
python audio_processing.py &
AUDIO_PID=$!

python cv_and_led.py &
CV_PID=$!

# Wait for either script to exit
wait -n $AUDIO_PID $CV_PID

# Once either script exits, clean up
cleanup
