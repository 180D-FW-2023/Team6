# SETTING UP BUFFER AND ASYNC PIPE READER

import threading
import pickle
import buffer_module as buffer
pipe_path = "audio_output"
data_buffer = DataBuffer(max_length=100, max_age=0.3)

def read_pipe(pipe_path):
    with open(pipe_path, 'rb') as pipe:  # Open the named pipe for binary reading
        while True:
            # Read a chunk of data from the pipe
            # NOTE: This example assumes that each pickle dump is small enough
            # to be read in a single .read() call, which might not always be the case.
            # For larger objects or variable-sized objects, you would need a more
            # robust method to determine the boundaries between serialized objects.
            serialized_data = pipe.read()
            if serialized_data:
                # Deserialize the data back into a Python object
                try:
                    data_tuple = pickle.loads(serialized_data)
                    # Update the buffer (or handle the data) with the deserialized object
                    buffer.add_to_buffer(data_tuple)
                except EOFError:
                    # Handle cases where partial data is read and causes pickle to fail
                    print("Incomplete data received, ignoring...")
                    continue

# Create and start the reader thread
reader_thread = threading.Thread(target=read_pipe, args=(pipe_path,))
reader_thread.daemon = True  # Daemonize thread
reader_thread.start()

# Main program continues from here
