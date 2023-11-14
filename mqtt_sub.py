import paho.mqtt.client as mqtt
import sqlite3

# Database setup
conn = sqlite3.connect('piano_notes.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS notes (note TEXT)''')
conn.commit()

def on_message(client, userdata, message):
    note = str(message.payload.decode("utf-8"))
    c.execute("INSERT INTO notes (note) VALUES (?)", (note,))
    conn.commit()

client = mqtt.Client()
client.connect("test.mosquitto.org", 1883, 60)
client.subscribe("your_topic")

client.on_message = on_message
client.loop_forever()
