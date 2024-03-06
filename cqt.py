import numpy as np
import librosa
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

# Step 1: Load and preprocess audio signal
def load_audio(audio_file):
    y, sr = librosa.load(audio_file)
    return y, sr

# Step 2: Compute Constant-Q Transform (CQT)
def compute_cqt(y, sr):
    cqt = np.abs(librosa.cqt(y, sr=sr, bins_per_octave=36))
    print(cqt)
    plt.plot(cqt)
    plt.show()
    return cqt

# Step 3: Peak Detection
def detect_peaks(cqt):
    peaks = []
    for i in range(cqt.shape[1]):
        cqt_slice = cqt[:, i]
        peak_idxs, _ = find_peaks(cqt_slice, prominence=0.1)
        peaks.append(peak_idxs)
        print(peaks)
    return peaks

# Step 4: Pitch Estimation
def estimate_pitches(peaks, sr):
    pitches = []
    for peak_idxs in peaks:
        for idx in peak_idxs:
            freq = librosa.cqt_frequencies(36, fmin=1)[idx]
            pitch = librosa.hz_to_note(freq)
            pitches.append(pitch)
    return pitches

# Step 5: Post-processing (optional)

# Main function
def polyphonic_pitch_detection(audio_file):
    # Step 1: Load and preprocess audio signal
    y, sr = load_audio(audio_file)
    
    # Step 2: Compute Constant-Q Transform (CQT)
    cqt = compute_cqt(y, sr)
    
    # Step 3: Peak Detection
    peaks = detect_peaks(cqt)
    
    # Step 4: Pitch Estimation
    pitches = estimate_pitches(peaks, sr)
    
    return pitches

# Example usage
audio_file = 'recorded_audio_cmaj.wav'
pitches = polyphonic_pitch_detection(audio_file)
print("Estimated pitches:", pitches)
