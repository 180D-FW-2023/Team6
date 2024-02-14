import paho.mqtt.client as mqtt
import led_module as led
# import audio_module as audio
from rpi_ws281x import Color
import zmq

'''
modes:
0 = default
1 = lesson
2 = test
'''

target_notes = []
played_notes = []
mode = 0 

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
    global target_notes, mode
    
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
    print(target_notes)
    
    match topic:
        case "team6/lesson":
            mode = 1
            # set first color to blue
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


################## MAIN LOOP #####################

print("Initializing LED strip")
led.start_sequence()

def lesson_mode(top_note):
    global mode, target_notes, played_notes
    
    print("TARGET ", target_notes)
    print("RECORDED ", played_notes)
    
    if top_note == target_notes[len(played_notes)]:
        print("Correct!")
        led.setColorByIndex(led.note_to_led_index[target_notes[len(played_notes)]], color=Color(0,128,0))
        played_notes.append(notes[0])
    else:
        print("Wrong!")
    
    
    if len(played_notes) == len(target_notes):
        print("Finished!")
        mode = 0
        led.start_sequence()
        played_notes = []
        target_notes = []
    else:
        # sets next note to blue
        led.setColorByIndex(led.note_to_led_index[target_notes[len(played_notes)]], color=Color(0,0,128))


def test_mode(top_note):
    global mode, target_notes, played_notes
    
    print("TARGET ", target_notes)
    print("RECORDED ", played_notes)
    
    if testModeCheckDup(top_note):
        return
    
    
    if top_note == target_notes[len(played_notes)]:
        print("Correct!")
        led.multiColor([led.note_to_led_index[target_notes[len(played_notes)]]], color=Color(0,128,0))
        # led.setColorByIndex(led.note_to_led_index[target_notes[len(played_notes)]], color=Color(0,128,0))
    else:
        print("Wrong!")
        led.multiColor([led.note_to_led_index[target_notes[len(played_notes)]]], color=Color(128,0,0))
        # led.setColorByIndex(led.note_to_led_index[target_notes[len(played_notes)]], color=Color(128,0,0))
    
    played_notes.append(top_note)
    
    if len(played_notes) == len(target_notes):
        print("Finished!")
        result = ''
        for i in played_notes:
            result += i + ' '
        print(result)
        client.publish('team6/test/results', result, qos=1)
        mode = 0
        led.start_sequence()
        played_notes = []
        target_notes = []

context = zmq.Context()
# Socket to subscribe to messages
subscriber = context.socket(zmq.PULL)
subscriber.bind("tcp://*:5556")

try:
    while True:
        l = ""
        try:
            l = subscriber.recv_string(zmq.NOBLOCK)  # Non-blocking receive
        except zmq.Again:
            # No message received, skip without blocking
            pass
        
        if not l:
            continue
        
        notes = [note.strip().upper() for note in l.split()]
        top_note = notes[0] if notes else None

        if top_note:
            
            match mode:
                case 1:
                    # lesson mode
                    print("----- Lesson mode -----")
                    print("top_note: ", top_note)
                    lesson_mode(top_note)
                case 2:
                    # test mode
                    print("----- Test mode -----")
                    test_mode(top_note)
                case _:
                    # default note playing - shows white light
                    print("----- Default mode -----")
                    # led.showOneColorOnly(led.note_to_led_index[top_note], color=Color(128,128,128),wait_ms=200)
                    led.turnOffExpired()
                    indices = [led.note_to_led_index[note] for note in notes]
                    led.multiColor(indices, color=Color(128,128,128))

except KeyboardInterrupt:
    # audio.cleanup()
    led.colorWipeAll(Color(128,0,0), 50)
    led.colorWipeAll(Color(0,0,0), 50)
    client.disconnect
    client.loop_stop()