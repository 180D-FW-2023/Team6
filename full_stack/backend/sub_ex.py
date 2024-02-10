import paho.mqtt.client as mqtt

# MQTT settings
MQTT_BROKER = 'test.mosquitto.org'  # Change to your MQTT broker address
MQTT_PORT = 1883           # Change to your MQTT broker port
MQTT_TOPIC = 'team6/test'           # Subscribe to all topics; change as needed

# The callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(MQTT_TOPIC)

# The callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    print(f"Received message: '{msg.payload.decode()}' on topic '{msg.topic}'")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Blocking call that processes network traffic, dispatches callbacks, and handles reconnecting
client.loop_forever()
