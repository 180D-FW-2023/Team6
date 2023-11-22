import paho.mqtt.client as mqtt
import sqlite3

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker as subscriber")
        client.subscribe("your_topic")
    else:
        print("Failed to connect, return code %d\n", rc)

def on_message(client, userdata, message):
    note = str(message.payload.decode("utf-8"))
    c.execute("INSERT INTO notes (note) VALUES (?)", (note,))
    conn.commit()

# Database setup
conn = sqlite3.connect('piano_notes.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS notes (note TEXT)''')
conn.commit()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect("test.mosquitto.org", 1883, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("Subscriber stopped")
finally:
    conn.close()
