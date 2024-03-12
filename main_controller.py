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

RED = Color(255,0,0)
GREEN = Color(0,255,0)
BLUE = Color(0,0,255)
WHITE = Color(255,255,255)
BLACK = Color(0,0,0)

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
    
    led.colorWipeAll(BLUE, wait_ms=25)
    led.colorWipeAll(GREEN, wait_ms=25)
    led.colorWipeAll(RED, wait_ms=25)
    led.colorWipeAll(wait_ms=50)
    
    topic = str(message.topic)
    msg = str(message.payload.decode("utf-8","ignore"))
    msg = msg.replace('#', '♯')
    print('Received message: "' + msg + '" on topic "' +
            message.topic + '" with QoS ' + str(message.qos))
    
    target_notes = msg.split()
    played_notes = []
    chord = len(target_notes) == 3
    print(target_notes)
    
    match topic:
        case "team6/lesson":
            mode = 1
            # set first color to blue
            if chord:
                # Chord mode
                led.setColorByIndices([led.note_to_led_index[note] for note in target_notes], color=BLUE)
            else:
                # Scales mode
                led.setColorByIndices([led.note_to_led_index[target_notes[0]]], color=BLUE)
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

def finish_mode_cleanup(delay=0.5):
    global mode, played_notes, target_notes, test_timer, chord
    print("Finished ", 'test' if mode == 2 else 'lesson', " mode!")
    played_notes = []
    target_notes = []
    mode = 0
    chord = False
    if test_timer:
        test_timer = None
    time.sleep(delay)
    led.start_sequence()
    
def lesson_mode(notes):
    global mode, target_notes, played_notes, chord
    
    if chord:
        # for note in notes:
        #     led.setRecentlyOn(led.note_to_led_index[note])
        correct_indices = [led.note_to_led_index[note] for note in notes if note in target_notes]
        wrong_indices = [led.note_to_led_index[note] for note in notes if note not in target_notes]
        led.multiColor(correct_indices, color=GREEN)
        led.multiColor(wrong_indices, color=RED)
        
        valid_notes = led.getNotesWithinInterval(time_interval=1)
        if len(valid_notes) == len(target_notes) and set(valid_notes) == set(target_notes):
            finish_mode_cleanup(1)
        else:
            print("Wrong: ", valid_notes)
    
    else:
        
        print("TARGET ", target_notes)
        print("RECORDED ", played_notes)
        
        top_note = notes[0]
        if top_note == target_notes[len(played_notes)]:
            print("Correct Note:", top_note)
            led.setColorByIndices([led.note_to_led_index[top_note]], color=GREEN)
            played_notes.append(top_note)
        else:
            led.multiColor([led.note_to_led_index[top_note]], color=RED)
            print("Wrong Note:", top_note)
        
        if len(played_notes) == len(target_notes):
            print("Lesson Completed!")
            finish_mode_cleanup()
        else:
            # sets next note to blue
            led.setColorByIndices([led.note_to_led_index[target_notes[len(played_notes)]]], color=BLUE)


test_timer = None

def check_time_elapsed(elapsed_seconds=2):
    global test_timer
    if test_timer and (datetime.now() - test_timer).total_seconds() > elapsed_seconds:
        return True
    return False

def test_mode(notes):
    global mode, target_notes, played_notes, chord, test_timer
    
    if chord:
        if not test_timer:
            test_timer = datetime.now()
        
        for note in notes:
            if not led.testModeCheckDup(note):
                if note not in target_notes:
                    print("Wrong note:", note)
                    led.multiColor([led.note_to_led_index[note]], color=RED)
                else:
                    print("Right note:", note)
                    led.multiColor([led.note_to_led_index[note]], color=GREEN)
        
        played_notes = led.getNotesWithinInterval(time_interval=2)
        
        if set(played_notes) == set(target_notes) and len(played_notes) == len(target_notes):
            print('PASSED')
            result = ' '.join(played_notes)
            print(result)
            client.publish('team6/test/results', result, qos=1)
            finish_mode_cleanup(1.5)
            return
        
        
        if any(note not in target_notes for note in played_notes) or check_time_elapsed():
            print('FAILED')
            result = ' '.join(played_notes)
            print(result)
            client.publish('team6/test/results', result, qos=1)
            finish_mode_cleanup(1.5)
            return
    
    else:
        print("TARGET ", target_notes)
        print("RECORDED ", played_notes)
        
        top_note = notes[0]
        
        if led.testModeCheckDup(led.note_to_led_index[top_note], time_diff = 2):
            return
        
        
        if top_note == target_notes[len(played_notes)]:
            print("Correct!")
            led.multiColor([led.note_to_led_index[target_notes[len(played_notes)]]], color=GREEN)
        else:
            print("Wrong!")
            led.multiColor([led.note_to_led_index[target_notes[len(played_notes)]]], color=RED)
        
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
        if mode == 0:       # default mode
            led.resetExpired(on_time = 0.4)
            
        if mode == 1:       # lesson mode
            led.resetExpired(on_time = 1, off_color=GREEN, indices = [led.note_to_led_index[note] for note in played_notes])      # first reset correctly played notes back to green, which sets its timestamp to None
            led.resetExpired(on_time = 1, off_color=BLUE, indices = [led.note_to_led_index[note] for note in target_notes])      # reset target notes back to blue
            led.resetExpired(on_time = 1, off_color=BLACK)      # turn off all other notes
        
        if chord and mode == 2 and test_timer and check_time_elapsed():
            test_mode([])

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
                    indices = [led.note_to_led_index[note] for note in notes]
                    led.multiColor(indices, color=WHITE)

except KeyboardInterrupt:
    # audio.cleanup()
    led.colorWipeAll(Color(128,0,0), 50)
    led.colorWipeAll(BLACK, 50)
    client.disconnect
    client.loop_stop()