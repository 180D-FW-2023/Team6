from collections import deque
import time

class DataBuffer:
    def __init__(self, max_length=100, max_age=0.3):
        self.buffer = deque(maxlen=max_length)
        self.max_age = max_age  # Maximum age of entries in seconds

    def add_to_buffer(self, data_tuple):
        """Add new data entry to the buffer."""
        timestamp, data = data_tuple
        self.buffer.append((timestamp, data))
        self.cleanup()

    def cleanup(self):
        """Remove old entries."""
        current_time = time.time()
        while self.buffer and current_time - self.buffer[0][0] > self.max_age:
            self.buffer.popleft()

    def get_latest_entry(self):
        """Return the data of the latest entry if buffer is not empty."""
        if self.buffer:
            return self.buffer[-1][1]
        return None