#! /usr/bin/env python

# Use pyaudio to open the microphone and run aubio.pitch on the stream of
# incoming samples. If a filename is given as the first argument, it will
# record 5 seconds of audio to this location. Otherwise, the script will
# run until Ctrl+C is pressed.

# Examples:
#    $ ./python/demos/demo_pyaudio.py
#    $ ./python/demos/demo_pyaudio.py /tmp/recording.wav

import time

import pyaudio
import sys
import numpy as np
import aubio
import librosa
from collections import OrderedDict
import math
import zmq
import collections
from datetime import datetime, timedelta
TWELVE_ROOT_OF_2 = math.pow(2, 1.0 / 12)


# initialise pyaudio
p = pyaudio.PyAudio()

FFT_SIZE = 4096
SAMPLE_RATE = 44100
# open stream
buffer_size = FFT_SIZE
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = SAMPLE_RATE
stream = p.open(format=pyaudio_format,
                channels=n_channels,
                rate=samplerate,
                input=True,
                frames_per_buffer=buffer_size)

if len(sys.argv) > 1:
    # record 5 seconds
    output_filename = sys.argv[1]
    record_duration = 5 # exit 1
    outputsink = aubio.sink(sys.argv[1], samplerate)
    total_frames = 0
else:
    # run forever
    outputsink = None
    record_duration = None

# setup pitch
tolerance = 0.8
win_s = FFT_SIZE # fft size
hop_s = buffer_size # hop size
pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(tolerance)
o = aubio.onset("default", win_s, hop_s, samplerate)
onsets = []
max_buffer = [0]
buf_const = 2
fft_len = FFT_SIZE

def divide_buffer_into_non_overlapping_chunks(buffer, max_len):
    buffer_len = len(buffer)
    chunks = int(buffer_len / max_len)
    #print("buffers_num: " + str(chunks))
    division_pts_list = []
    for i in range(1, chunks):
        division_pts_list.append(i * max_len)    
    splitted_array_view = np.split(buffer, division_pts_list, axis=0)
    return splitted_array_view

def getFFT(data, rate):
    # Returns fft_freq and fft, fft_res_len.
    len_data = len(data)
    data = data * np.hamming(len_data)
    fft = np.fft.rfft(data)
    fft = np.abs(fft)
    ret_len_FFT = len(fft)
    freq = np.fft.rfftfreq(len_data, 1.0 / rate)
    # return ( freq[:int(len(freq) / 2)], fft[:int(ret_len_FFT / 2)], ret_len_FFT )
    return ( freq, fft, ret_len_FFT )

def remove_dc_offset(fft_res):
    # Removes the DC offset from the FFT (First bin's)
    fft_res[0] = 0.0
    fft_res[1] = 0.0
    fft_res[2] = 0.0
    return fft_res

def freq_for_note(base_note, note_index):
    # See Physics of Music - Notes
    #     https://pages.mtu.edu/~suits/NoteFreqCalcs.html
    
    A4 = 440.0

    base_notes_freq = {"A2" : A4 / 4,   # 110.0 Hz
                       "A3" : A4 / 2,   # 220.0 Hz
                       "A4" : A4,       # 440.0 Hz
                       "A5" : A4 * 2,   # 880.0 Hz
                       "A6" : A4 * 4 }  # 1760.0 Hz  

    scale_notes = { "C"  : -9.0,
                    "C#" : -8.0,
                    "D"  : -7.0,
                    "D#" : -6.0,
                    "E"  : -5.0,
                    "F"  : -4.0,
                    "F#" : -3.0,
                    "G"  : -2.0,
                    "G#" : -1.0,
                    "A"  :  1.0,
                    "A#" :  2.0,
                    "B"  :  3.0,
                    "Cn" :  4.0}

    scale_notes_index = list(range(-9, 5)) # Has one more note.
    note_index_value = scale_notes_index[note_index]
    freq_0 = base_notes_freq[base_note]
    freq = freq_0 * math.pow(TWELVE_ROOT_OF_2, note_index_value) 
    return freq

def get_all_notes_freq():
    ordered_note_freq = []
    ordered_notes = ["C",
                     "C♯",
                     "D",
                     "D♯",
                     "E",
                     "F",
                     "F♯",
                     "G",
                     "G♯",
                     "A",
                     "A♯",
                     "B"]
    for octave_index in range(2, 7):
        base_note  = "A" + str(octave_index)
        # note_index = 0  # C2
        # note_index = 12  # C3
        for note_index in range(0, 12):
            note_freq = freq_for_note(base_note, note_index)
            note_name = ordered_notes[note_index] + str(octave_index)
            ordered_note_freq.append((note_name, note_freq))
    return ordered_note_freq

def find_nearest_note(ordered_note_freq, freq):
    final_note_name = 'note_not_found'
    last_dist = 1_000_000.0
    for note_name, note_freq in ordered_note_freq:
        curr_dist = abs(note_freq - freq)
        if curr_dist < last_dist:
            last_dist = curr_dist
            final_note_name = note_name
        elif curr_dist > last_dist:
            break    
    return final_note_name

def PitchSpectralHps(X, freq_buckets, f_s, buffer_rms):

    """
    NOTE: This function is from the book Audio Content Analysis repository
    https://www.audiocontentanalysis.org/code/pitch-tracking/hps-2/
    The license is MIT Open Source License.
    And I have modified it. Go to the link to see the original.

    computes the maximum of the Harmonic Product Spectrum

    Args:
        X: spectrogram (dimension FFTLength X Observations)
        f_s: sample rate of audio data

    Returns:
        f HPS maximum location (in Hz)
    """

    # initialize
    iOrder = 4
    f_min = 65.41   # C2      300
    # f = np.zeros(X.shape[1])
    f = np.zeros(len(X))

    iLen = int((X.shape[0] - 1) / iOrder)
    afHps = X[np.arange(0, iLen)]
    k_min = int(round(f_min / f_s * 2 * (X.shape[0] - 1)))

    # compute the HPS
    for j in range(1, iOrder):
        X_d = X[::(j + 1)]
        afHps *= X_d[np.arange(0, iLen)]

    ## Uncomment to show the original algorithm for a single frequency or note. 
    # f = np.argmax(afHps[np.arange(k_min, afHps.shape[0])], axis=0)
    ## find max index and convert to Hz
    # freq_out = (f + k_min) / (X.shape[0] - 1) * f_s / 2

    note_threshold = note_threshold_scaled_by_RMS(buffer_rms)

    all_freq = np.argwhere(afHps[np.arange(k_min, afHps.shape[0])] > note_threshold)
    # find max index and convert to Hz
    freqs_out = (all_freq + k_min) / (X.shape[0] - 1) * f_s / 2

    
    x = afHps[np.arange(k_min, afHps.shape[0])]
    freq_indexes_out = np.where( x > note_threshold)
    freq_values_out = x[freq_indexes_out]

    # print("\n##### x: " + str(x))
    # print("\n##### freq_values_out: " + str(freq_values_out))

    max_value = np.max(afHps[np.arange(k_min, afHps.shape[0])])
    max_index = np.argmax(afHps[np.arange(k_min, afHps.shape[0])])
    
    ## Uncomment to print the values: buffer_RMS, max_value, min_value
    ## and note_threshold.    
    #print(" buffer_rms: " + to_str_f4(buffer_rms) )
    #print(" max_value : " + to_str_f(max_value) + "  max_index : " + to_str_f(max_index) )
    #print(" note_threshold : " + to_str_f(note_threshold) )

    ## Uncomment to show the graph of the result of the 
    ## Harmonic Product Spectrum. 
    #fig, ax = plt.subplots()
    #yr_tmp = afHps[np.arange(k_min, afHps.shape[0])]
    #xr_tmp = (np.arange(k_min, afHps.shape[0]) + k_min) / (X.shape[0] - 1) * f_s / 2
    #ax.plot(xr_tmp, yr_tmp)
    #plt.show()

    # Turns 2 level list into a one level list.
    freqs_out_tmp = []
    for freq, value  in zip(freqs_out, freq_values_out):
        freqs_out_tmp.append((freq[0], value))
    
    return freqs_out_tmp

def note_threshold_scaled_by_RMS(buffer_rms):
    note_threshold = 1000.0 * (4 / 0.090) * buffer_rms / 2
    return note_threshold

def normalize(arr):
    # Note: Do not use.
    # Normalize array between -1 and 1.
    # Only works if the signal is larger then the final signal and if the positive
    # value is grater in absolute value them the negative value.
    ar_res = (arr / (np.max(arr) / 2)) - 1  
    return ar_res

def to_str_f(value):
    # Returns a string with a float without decimals.
    return "{0:.0f}".format(value)

def to_str_f4(value):
    # Returns a string with a float without decimals.
    return "{0:.4f}".format(value)

ordered_note_freq = get_all_notes_freq()

# Prepare the ZeroMQ context and PULL socket
context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.connect("tcp://localhost:5555")  # Connect to the sender
print("*** starting recording")





def add_message_to_buffer(message):
    now = datetime.now()
    message_buffer.append((message, now))
    while message_buffer:
        _, timestamp = message_buffer[0]  # Check the oldest message
        if now - timestamp > timedelta(seconds=0.3):
            message_buffer.popleft()
        else:
            break   
message_buffer = collections.deque()    


def get_pitches():
    try:
        audiobuffer = stream.read(buffer_size)
        signal = np.frombuffer(audiobuffer, dtype=np.float32)
        thresh = np.sum(max_buffer[-buf_const:]) / len(max_buffer)
        max_buffer = np.append(max_buffer, np.max(signal))
        max_buffer = max_buffer[-buf_const:]
        
        #aubio pitch
        '''
        pitch = pitch_o(signal)[0]
        confidence = pitch_o.get_confidence()
        note = aubio.midi2note(int(pitch)+1)
        print("{} / {}".format(note,confidence))
        '''


        #librosa pitch
        max_noise = np.max(np.abs(librosa.stft(signal, window = 'hamming')))
        # print("max_noise:" +  str(max_noise))
        oldD = librosa.amplitude_to_db(np.abs(librosa.stft(signal, window = 'hamming')), ref=np.max)
        mask = (oldD[:, -10:-1] > -70).all(1)
        blank = -80
        newD = np.full_like(oldD, blank)
        newD[mask] = oldD[mask]
        newS=librosa.db_to_amplitude(newD)

        pitches, magnitudes = librosa.piptrack(S=newS, sr=samplerate)
        #print(pitches[np.where(magnitudes>0)])
        #print(magnitudes[np.where(magnitudes>0)])
        pitches_final = pitches[np.asarray(magnitudes > 0.12).nonzero()]
        if len(pitches_final) > 0:
            notes_librosa = librosa.hz_to_note(pitches_final)
            notes_librosa = list(OrderedDict.fromkeys(notes_librosa))
        else:
            notes_librosa = []
        #print(pitches_final)
        #print(notes)
        l = " ".join(notes_librosa)
        
        if max_noise < 40:
            l = ""
            notes_librosa = []
        #print("Librosa: " + l)
        if (max_noise > 3):
            if o(signal):
                print("%f" % o.get_last_s())
                onsets.append(o.get_last())
        
        #HPS pitch
        buffer_chunks = divide_buffer_into_non_overlapping_chunks(signal, fft_len)
        # The buffer chunk at n seconds:

        count = 0
        
        correct_notes = set()
        
        #HPS
        ## Uncomment to process a single chunk os a limited number os sequential chunks. 
        #for chunk in buffer_chunks[5: 6]:
        for chunk in buffer_chunks[0: 60]:
            #print("\n...Chunk: ", str(count))
                    
            fft_freq, fft_res, fft_res_len = getFFT(chunk, len(chunk))
            fft_res = remove_dc_offset(fft_res)

            # Calculate Root Mean Square of the signal buffer, as a scale factor to the threshold.
            buffer_rms = np.sqrt(np.mean(chunk**2))

            all_freqs = PitchSpectralHps(fft_res, fft_freq, samplerate, buffer_rms)
            # print("all_freqs ")
            # print(all_freqs)
            notes_hps = []
            for freq in all_freqs:
                note_name = find_nearest_note(ordered_note_freq, freq[0])
                #print("=> freq: " + to_str_f(freq[0]) + " Hz  value: " + to_str_f(freq[1]) + " note_name: " + note_name )
                notes_hps.append(note_name)

            notes_hps_string = " ".join(notes_hps)
            #print("HPS:" + notes_hps_string)

            count += 1
            both_notes = []
            note_pairs = [("C3", "C4"), ("C♯3", "C♯4"), ("D3", "D4"), ("D♯3", "D♯4"), ("E3", "E4"), ("F3", "F4"), ("F♯3", "F♯4"), ("G3", "G4"), ("G♯3", "G♯4"), ("A3", "A4"), ("A♯3", "A♯4"), ("B3", "B4")]
            for pair in note_pairs:
                letter1, letter2 = pair
                # Check if the extracted letters match and append if conditions are met
                if letter1 in notes_hps and letter2 in notes_librosa:
                    #print(pair)
                    both_notes.append(letter1)
            for nl in notes_librosa:
                if nl in notes_hps:
                    both_notes.append(nl)
            
            #remove duplicates
            # print("librosa: ", notes_librosa)
            # print("hps: ", notes_hps)
            both_notes = list(set(both_notes))
            both_notes_string = " ".join(both_notes)
        

            try:
                notes_string = socket.recv_string(zmq.NOBLOCK)  # Non-blocking receive
                add_message_to_buffer(notes_string)
            except zmq.Again:
                # No message received, skip without blocking
                pass

            print("Combined:" + both_notes_string)    
            # Define the message buffer
            

            if both_notes_string:
                # print("Msg buffer: ", message_buffer)            
                audio_notes = both_notes_string.split()

                for audio in audio_notes:
                    
                    for message, _ in message_buffer:
                        if message == audio:
                            correct_notes.add(audio)
                            print(f"Audio note '{audio}' exists in the buffer.")

            #         if not audio_note_found:
            #             print(f"Audio note '{audio}' does not exist in the buffer.")
                print("Correct Notes: ", correct_notes)

            if outputsink:
                outputsink(signal, len(signal))

            if record_duration:
                total_frames += len(signal)
                if record_duration * samplerate < total_frames:
                    break
                
        if correct_notes:
            print("Correct notes: ", correct_notes)
            return correct_notes

    except:
        print("Somethign went wrong")
        
def cleanup():
    print("*** done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()