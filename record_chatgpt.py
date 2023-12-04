import sounddevice as sd
from scipy.io.wavfile import write

def record_audio(filename, duration, sample_rate=44100):
    # Record audio
    recording = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=2, dtype='int16')
    sd.wait()

    # Save the recorded audio to a WAV file
    write(filename, sample_rate, recording)

if __name__ == "__main__":
    # Set the filename and duration for recording
    output_filename = "recorded_audio.wav"
    recording_duration = 5  # in seconds

    # Record audio and save to WAV file
    record_audio(output_filename, recording_duration)
    
    print(f"Audio recorded and saved as {output_filename}")