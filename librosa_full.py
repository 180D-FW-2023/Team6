#import libraries
import sounddevice as sd
from scipy.io.wavfile import write
from scipy.io import wavfile
import librosa
import numpy as np
from collections import OrderedDict
np.set_printoptions(threshold=np.inf)
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import numpy as np
import math

# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connection returned result: "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("ece180d/test")
# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected Disconnect')
    else:
     print('Expected Disconnect')
# The default message callback.
# (won’t be used if only publishing, but can still exist)
def on_message(client, userdata, message):
    print('Received message: "' + str(message.payload) + '" on topic "' +
        message.topic + '" with QoS ' + str(message.qos))
# 1. create a client instance.
client = mqtt.Client()
# add additional client options (security, certifications, etc.)
# many default options should be good to start off.
# add callbacks to client.
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
# 2. connect to a broker using one of the connect*() functions.
client.connect_async('test.mosquitto.org')
# 3. call one of the loop*() functions to maintain network traffic flow with the broker.
client.loop_start()
# 4. use subscribe() to subscribe to a topic and receive messages.
# 5. use publish() to publish messages to the broker.
# payload must be a string, bytearray, int, float or None.


# 6. use disconnect() to disconnect from the broker.

fs = 22050  # Sample rate
seconds = 0.1 # Duration of recording
record = 1 #whether or not to record
i = 0
win_s = 1024 # fft size
hop_s = 441 # hop size
prev_l = ""
onsets = np.array([])

#Setus HPS
TWELVE_ROOT_OF_2 = math.pow(2, 1.0 / 12)
tolerance = 0.8
fft_len=1024

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
                     "C#",
                     "D",
                     "D#",
                     "E",
                     "F",
                     "F#",
                     "G",
                     "G#",
                     "A",
                     "A#",
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

#loop
while True:
    #record audio buffer
    if (record == 1):
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        sd.wait()  # Wait until recording is finished
        write('output.wav', fs, myrecording)  # Save as WAV file 


    sr, data = wavfile.read('output.wav')

    #filter audio buffer

    #y, sr = librosa.load('output.wav',sr=None)
    y = np.asarray(data).astype(float)
    #print(y.shape)
    oldS = np.abs(librosa.stft(y, window = 'hann'))
    max_noise = np.max(np.abs(oldS))
    oldD = librosa.amplitude_to_db(np.abs(librosa.stft(y, window='hann')), ref=np.max)
    mask = (oldD[:, -10:-1] > -21).all(1)
    blank = -80
    newD = np.full_like(oldD, blank)
    newD[mask] = oldD[mask]
    newS=librosa.db_to_amplitude(newD)

    #get pitches from filtered audio
    pitches, magnitudes = librosa.piptrack(S=newS, sr=sr)
    pitches_final = pitches[np.asarray(magnitudes > 0.12).nonzero()]
    if len(pitches_final) > 0:
        notes_librosa = librosa.hz_to_note(pitches_final)
        notes_librosa = list(OrderedDict.fromkeys(notes_librosa))
    else:
        notes_librosa = ""
    l = " ".join(notes_librosa)
    

    '''
    fig, ax = plt.subplots()

    img = librosa.display.specshow(librosa.amplitude_to_db(newS,ref=np.max),y_axis='log', x_axis='time', ax=ax)

    ax.set_title('Power spectrogram')

    fig.colorbar(img, ax=ax, format="%+2.0f dB")

    ax.set_title('Power spectrogram')

    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    plt.show()
    '''
    
        #print("loop")
        #print(p)
    #print("max_noise" + str(max_noise))
    #print(first_or_None)
    if max_noise < 1:
        l = ""
        notes_librosa = []
    print("Librosa: " + l)

    #HPS pitch
    buffer_chunks = divide_buffer_into_non_overlapping_chunks(data, fft_len)
    # The buffer chunk at n seconds:

    count = 0
    
    ## Uncomment to process a single chunk os a limited number os sequential chunks. 
    #for chunk in buffer_chunks[5: 6]:
    for chunk in buffer_chunks[0: 60]:
        #print("\n...Chunk: ", str(count))
                
        fft_freq, fft_res, fft_res_len = getFFT(chunk, len(chunk))
        fft_res = remove_dc_offset(fft_res)

        # Calculate Root Mean Square of the signal buffer, as a scale factor to the threshold.
        buffer_rms = np.sqrt(np.mean(chunk**2))

        all_freqs = PitchSpectralHps(fft_res, fft_freq, sr, buffer_rms)
        # print("all_freqs ")
        # print(all_freqs)
        notes_hps = []
        for freq in all_freqs:
            note_name = find_nearest_note(ordered_note_freq, freq[0])
            #print("=> freq: " + to_str_f(freq[0]) + " Hz  value: " + to_str_f(freq[1]) + " note_name: " + note_name )
            notes_hps.append(note_name)

        notes_hps_string = " ".join(notes_hps)
        print("HPS:" + notes_hps_string)



        ## Uncomment to print the arrays.
        # print("\nfft_freq: ")
        # print(fft_freq)
        # print("\nfft_freq_len: " + str(len(fft_freq)))

        # print("\nfft_res: ")
        # print(fft_res)

        # print("\nfft_res_len: ")
        # print(fft_res_len)


        ## Uncomment to show the graph of the result of the FFT with the
        ## correct frequencies in the legend. 
        # N = fft_res_len
        # fft_freq_interval = fft_freq[: N // 4]
        # fft_res_interval = fft_res[: N // 4]
        # fig, ax = plt.subplots()
        # ax.plot(fft_freq_interval, 2.0/N * np.abs(fft_res_interval))
        # plt.show()

        count += 1
    both_notes = []
    for nl in notes_librosa:
        if 'B' in nl:
            both_notes.append(nl)
        if 'E' in nl:
            both_notes.append(nl)
        if nl in notes_hps:
            both_notes.append(nl)
    
    both_notes_string = " ".join(both_notes)
    print("Combined:" + both_notes_string)     

    client.publish('your_topic', l, qos=1)


    
    #get onset of notes and calculate tempo
    '''
    if o(np.float32(y)):
        print("%f" % o.get_last_s())
        onsets = np.append(onsets, o.get_last())
    '''
    cur_onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    if (cur_onsets != []):
        detected = True
    else:
        detected = False
    print(detected)
    if l != prev_l:
        np.append(onsets, i * seconds)
    np.append(onsets, cur_onsets)
    client.publish('your_topic', detected, qos=1)
    
    
    prev_l = l
    i = i + 1

client.loop_stop()
client.disconnect()
