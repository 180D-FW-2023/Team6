import paho.mqtt.client as mqtt
import time
import random

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def on_publish(client, userdata, result):
    print("Data published")

# MQTT setup
broker = "test.mosquitto.org"
port = 1883
topic = "your_topic"

# Create a client instance
client = mqtt.Client()

client.on_connect = on_connect
client.on_publish = on_publish

# Connect to the broker
try:
    client.connect(broker, port, 60)
    client.loop_start()

    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4']
    while True:
        note = random.choice(notes)
        result = client.publish(topic, note)
        status = result.rc
        if status == mqtt.MQTT_ERR_SUCCESS:
            print(f"Sent: {note}")
        elif status == mqtt.MQTT_ERR_NO_CONN:
            print("No connection to the broker")
        time.sleep(0.3)

except KeyboardInterrupt:
    print("Test finished")
finally:
    client.loop_stop()
    client.disconnect()
