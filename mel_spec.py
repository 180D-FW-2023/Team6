import numpy as np
import librosa
from scipy.signal import find_peaks

# Step 1: Load and preprocess audio signal
def load_audio(audio_file):
    y, sr = librosa.load(audio_file)
    return y, sr

# Step 2: Compute Mel spectrogram
def compute_mel_spectrogram(y, sr):
    mel_spectrogram = librosa.feature.melspectrogram(y=y, sr=sr)
    return mel_spectrogram

# Step 3: Peak Detection in Mel spectrogram
def detect_peaks(mel_spectrogram):
    peaks = []
    for i in range(mel_spectrogram.shape[0]):
        mel_slice = mel_spectrogram[:, i]
        peak_idxs, _ = find_peaks(mel_slice, prominence=0.1)
        peaks.append(peak_idxs)
    return peaks

# Step 4: Convert peak indices to frequencies
def peak_indices_to_frequencies(peaks, sr):
    frequencies = []
    for peak_idxs in peaks:
        freqs = librosa.mel_frequencies(n_mels=len(peak_idxs), fmin=0, fmax=sr/2)
        frequencies.append(freqs)
    return frequencies

# Step 5: Convert frequencies to MIDI pitches
def frequencies_to_pitches(frequencies):
    pitches = []
    for freqs in frequencies:
        pitches.append(librosa.hz_to_note(freqs))
    return pitches

# Main function
def polyphonic_pitch_detection(audio_file):
    # Step 1: Load and preprocess audio signal
    y, sr = load_audio(audio_file)
    
    # Step 2: Compute Mel spectrogram
    mel_spectrogram = compute_mel_spectrogram(y, sr)
    
    # Step 3: Peak Detection in Mel spectrogram
    peaks = detect_peaks(mel_spectrogram)
    
    # Step 4: Convert peak indices to frequencies
    frequencies = peak_indices_to_frequencies(peaks, sr)
    
    # Step 5: Convert frequencies to MIDI pitches
    pitches = frequencies_to_pitches(frequencies)
    
    return pitches

# Example usage
audio_file = 'recorded_audio.wav'
pitches = polyphonic_pitch_detection(audio_file)
print("Estimated pitches:", pitches)