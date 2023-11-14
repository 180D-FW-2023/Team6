import paho.mqtt.client as mqtt
import time
import random

# MQTT setup
broker = "test.mosquitto.org"
port = 1883
topic = "your_topic"

# Create a client instance
client = mqtt.Client()

# Connect to the broker
client.connect(broker, port, 60)

# Publish test messages
notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4']
try:
    while True:
        # Randomly pick a note to simulate pitch detection
        note = random.choice(notes)
        client.publish(topic, note)
        print(f"Sent: {note}")
        time.sleep(2)  # Send a note every 2 seconds
except KeyboardInterrupt:
    print("Test finished")
