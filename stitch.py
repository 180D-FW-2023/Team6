import wave
import numpy as np

def duplicate_and_stitch_wav(input_file, output_file, num_duplicates):
    # Open the input file
    with wave.open(input_file, 'rb') as original_wav:
        # Get the parameters of the input WAV file
        params = original_wav.getparams()
        
        # Read the data from the input WAV file
        original_data = original_wav.readframes(original_wav.getnframes())
        
        # Duplicate the data
        duplicated_data = np.tile(np.frombuffer(original_data, dtype=np.int16), num_duplicates)
        
        # Open the output file for writing
        with wave.open(output_file, 'wb') as output_wav:
            # Set the parameters for the output WAV file
            output_wav.setparams(params)
            
            # Write the duplicated data to the output WAV file
            output_wav.writeframes(duplicated_data.tobytes())

# Example usage:
input_file = 'recorded_audio.wav'
output_file = 'output.wav'
num_duplicates = 3  # Adjust this according to how many times you want to duplicate the file

duplicate_and_stitch_wav(input_file, output_file, num_duplicates)