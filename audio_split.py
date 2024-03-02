import os
import numpy as np
import matplotlib.pyplot as plt
import librosa.display
from pydub import AudioSegment

def split_audio_and_save_mel_spectrograms(audio_file, output_folder, chunk_size_ms=50):
    audio = AudioSegment.from_file(audio_file)
    chunk_size = chunk_size_ms  # in milliseconds
    total_duration = len(audio)

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    for i in range(0, total_duration, chunk_size):
        start = i
        end = min(i + chunk_size, total_duration)
        chunk = audio[start:end]

        # Convert to numpy array
        samples = np.array(chunk.get_array_of_samples())
        # Normalize
        samples = samples / np.max(np.abs(samples))
        # Get the sample rate
        sr = chunk.frame_rate
        #print(sr)
        # Get Mel spectrogram
        mel_spec = librosa.feature.melspectrogram(y=samples, sr=sr)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        plt.figure(figsize=(6, 4))
        librosa.display.specshow(mel_spec_db, sr=sr, fmax=1024, x_axis='time', y_axis='mel')
        #plt.colorbar(format='%+2.0f dB')
        #plt.title('Mel Spectrogram')
        plt.axis('off')
        plt.savefig(os.path.join(output_folder, f"mel_spectrogram_d_chunk_{start}.png"), bbox_inches='tight', pad_inches=0)
        plt.close()

# Example usage:
audio_file = "recorded_audio.wav"  # Update with your audio file path
output_folder = "output_mel_spectrograms_d"  # Folder where the mel spectrograms will be saved
split_audio_and_save_mel_spectrograms(audio_file, output_folder, chunk_size_ms=50)
