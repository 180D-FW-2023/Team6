import numpy as np
import scipy.io.wavfile as wav
import scipy
from scipy.fftpack import fft, ifft
import matplotlib.pyplot as plt

def cepstral_pitch_detection(signal, fs, frame_size=2048, hop_size=512, threshold=0.2):
    # Compute the magnitude spectrum of the signal
    _, _, Zxx = scipy.signal.stft(signal, fs=fs, nperseg=frame_size, noverlap=hop_size)
    magnitude_spectrum = np.abs(Zxx)

    # Compute the cepstrum by taking the inverse Fourier transform of the log magnitude spectrum
    log_magnitude_spectrum = np.log(np.maximum(magnitude_spectrum, 1e-10))
    cepstrum = np.real(ifft(log_magnitude_spectrum, axis=0))
    print(cepstrum)
    plt.plot(cepstrum)
    #print(cepstrum)
    # Find peaks in the cepstrum
    peaks, _ = scipy.signal.find_peaks(cepstrum[0], height=threshold)

    # Convert peak indices to frequencies
    frequencies = fs / (hop_size * peaks)
    plt.show()
    return frequencies

# Example usage
if __name__ == "__main__":
    # Load an example audio file (replace 'your_audio_file.wav' with the actual file path)
    fs, audio_data = wav.read('recorded_audio.wav')

    # Convert audio data to mono if it's stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Normalize the audio data
    audio_data = audio_data / np.max(np.abs(audio_data))

    # Perform polyphonic pitch detection using cepstral analysis
    detected_frequencies = cepstral_pitch_detection(audio_data, fs)

    print("Detected Frequencies: {}".format(detected_frequencies))