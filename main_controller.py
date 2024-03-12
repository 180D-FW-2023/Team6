import paho.mqtt.client as mqtt
import led_module as led
# import audio_module as audio
from rpi_ws281x import Color
import zmq
from datetime import datetime, timedelta
import time

'''
modes:
0 = default
1 = lesson
2 = test
'''

target_notes = []
played_notes = []
mode = 0 
chord = False

################## MQTT SETUP #####################

# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connection returned result: "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("team6/lesson")
    client.subscribe("team6/test")

# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected Disconnect')
    else:
        print('Expected Disconnect')

def on_message(client, userdata, message):
    global target_notes, played_notes, mode, chord
    
    led.colorWipeAll(Color(128,0,0), wait_ms=50)
    led.colorWipeAll(Color(0,128,0), wait_ms=50)
    led.colorWipeAll(Color(0,0,128), wait_ms=50)
    led.colorWipeAll(wait_ms=50)
    
    topic = str(message.topic)
    scale = str(message.payload.decode("utf-8","ignore"))
    print('Received message: "' + str(message.payload) + '" on topic "' +
            message.topic + '" with QoS ' + str(message.qos))
    
    target_notes = scale.split()
    played_notes = []
    chord = len(target_notes) == 3
    print(target_notes)
    
    match topic:
        case "team6/lesson":
            mode = 1
            # set first color to blue
            if chord:
                # Chord mode
                led.multiColor([led.note_to_led_index[note] for note in target_notes], color=Color(0,0,128))
            else:
                # Scales mode
                led.showOneColorOnly(led.note_to_led_index[target_notes[0]], color=Color(0,0,128))
        case "team6/test":
            mode = 2
        case _:
            mode = 0
            
    
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
client.loop_start()

###################### MODES SETUP ######################

print("Initializing LED strip")
led.start_sequence()
recently_on = []    # TODO: consider combining this with played_notes

def set_note_on(note):
    global recently_on
    now = datetime.now()
    recently_on.append((note, now))


def check_target_notes_within_interval(time_interval=0.5):
    global recently_on, target_notes
    now = datetime.now()

    # Filter out notes not within the TIME_INTERVAL
    valid_notes = [(note, timing) for note, timing in recently_on if now - timing <= timedelta(seconds=time_interval)]

    # Check if there are exactly 3 target notes within the interval
    if len(valid_notes) == 3:
        played_notes = {note for note, _ in valid_notes}
        
        # Check if played notes match target notes exactly
        if sorted(played_notes) == sorted(target_notes):
            return True

    # If there are more than 3 notes or the notes don't match the target notes
    return False

def finish_mode_cleanup(delay=0.5):
    global mode, played_notes, target_notes, test_timer
    print("Finished ", 'test' if mode == 2 else 'lesson', " mode!")
    time.sleep(delay)
    mode = 0
    led.start_sequence()
    played_notes = []
    target_notes = []
    if test_timer:
        test_timer = None
    
def lesson_mode(notes):
    global mode, target_notes, played_notes, chord
    
    if chord:
        for note in notes:
            set_note_on(note)
        result = check_target_notes_within_interval()
        if result:
            finish_mode_cleanup(1)
        else:
            print("Failed: ", recently_on)
    else:
        print("TARGET ", target_notes)
        print("RECORDED ", played_notes)
        
        top_note = notes[0]
        if top_note == target_notes[len(played_notes)]:
            print("Correct!")
            led.setColorByIndex(led.note_to_led_index[target_notes[len(played_notes)]], color=Color(0,128,0))
            played_notes.append(top_note)
        else:
            print("Wrong!")
        
        if len(played_notes) == len(target_notes):
            finish_mode_cleanup()
        else:
            # sets next note to blue
            led.setColorByIndex(led.note_to_led_index[target_notes[len(played_notes)]], color=Color(0,0,128))


test_timer = None

def start_test_timer():
    global test_timer
    test_timer = datetime.now()

def check_time_elapsed(elapsed_seconds=2):
    global test_timer
    if test_timer and (datetime.now() - test_timer).total_seconds() > elapsed_seconds:
        return True
    return False

def test_mode(notes):
    global mode, target_notes, played_notes, chord, test_timer
    
    if chord:
        # Check for the first note and start the timer
        if not test_timer:
            # Assuming the first note in the list is the start
            start_test_timer()
            for note in notes:
                if not led.testModeCheckDup(note):
                    played_notes.append(note)
                    if note not in target_notes:
                        print("Wrong!")
                        led.multiColor([led.note_to_led_index[note]], color=Color(255,0,0))
                    else:
                        print("Right!")
                        led.multiColor([led.note_to_led_index[note]], color=Color(0,255,0))
            return
        
        if check_time_elapsed():
            # Check if the correct notes are played
            if set(played_notes) == set(target_notes) and len(played_notes) == len(target_notes):
                # If correct notes are played, end the test
                result = ' '.join(sorted(played_notes))
                client.publish('team6/test/results', result, qos=1)
                finish_mode_cleanup(1.5)
            else:
                result = ' '.join(sorted(played_notes))
                client.publish('team6/test/results', result, qos=1)
                finish_mode_cleanup(1.5)
        else:
            # If timer hasn't elapsed, keep adding notes
            for note in notes:
                if not led.testModeCheckDup(note):
                    played_notes.append(note)
                    if note not in target_notes:
                        print("Wrong!")
                        led.multiColor([led.note_to_led_index[note]], color=Color(255,0,0))
                    else:
                        print("Right!")
                        led.multiColor([led.note_to_led_index[note]], color=Color(0,255,0))
    
    else:
        print("TARGET ", target_notes)
        print("RECORDED ", played_notes)
        
        top_note = notes[0]
        
        if led.testModeCheckDup(top_note, time_diff = 1.5):
            return
        
        
        if top_note == target_notes[len(played_notes)]:
            print("Correct!")
            led.multiColor([led.note_to_led_index[target_notes[len(played_notes)]]], color=Color(0,255,0))
        else:
            print("Wrong!")
            led.multiColor([led.note_to_led_index[target_notes[len(played_notes)]]], color=Color(255,0,0))
        
        played_notes.append(top_note)
        
        if len(played_notes) == len(target_notes):
            result = ''
            for i in played_notes:
                result += i + ' '
            print(result)
            client.publish('team6/test/results', result, qos=1)
            finish_mode_cleanup()

context = zmq.Context()
# Socket to subscribe to messages
subscriber = context.socket(zmq.PULL)
subscriber.bind("tcp://*:5556")

################## MAIN LOOP #####################

try:
    while True:
        if mode == 0:
            led.turnOffExpired(on_time = 0.2)

        l = ""
        try:
            l = subscriber.recv_string(zmq.NOBLOCK)  # Non-blocking receive
        except zmq.Again:
            # No message received, skip without blocking
            pass
        
        if not l:
            continue
        
        notes = [note.strip().upper() for note in l.split()]

        if notes:
            
            match mode:
                case 1:
                    # lesson mode
                    print("----- Lesson mode -----")
                    lesson_mode(notes)
                case 2:
                    # test mode
                    print("----- Test mode -----")
                    test_mode(notes)
                case _:
                    # default note playing - shows white light
                    print("----- Default mode -----")
                    # led.showOneColorOnly(led.note_to_led_index[top_note], color=Color(128,128,128),wait_ms=200)
                    indices = [led.note_to_led_index[note] for note in notes]
                    led.multiColor(indices, color=Color(128,128,128))

except KeyboardInterrupt:
    # audio.cleanup()
    led.colorWipeAll(Color(128,0,0), 50)
    led.colorWipeAll(Color(0,0,0), 50)
    client.disconnect
    client.loop_stop()