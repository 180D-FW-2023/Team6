from collections import deque
import time

# Initialize the buffer with a maximum length of 100 entries
buffer = deque(maxlen=100)

def add_to_buffer(data, timestamp):
    # Add new data entry to the buffer
    buffer.append((timestamp, data))
    # Remove old entries
    current_time = time.time()
    while buffer and current_time - buffer[0][0] > 0.3:
        buffer.popleft()

def get_latest_entry():
    # Return the latest entry if buffer is not empty
    if buffer:
        return buffer[-1]
    return None
