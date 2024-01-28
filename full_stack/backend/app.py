from flask import Flask, request, jsonify
from flask_mqtt import Mqtt
from flask_socketio import SocketIO

app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = 'test.mosquitto.org'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''  # Set this when verifying username and password
app.config['MQTT_PASSWORD'] = ''  # Set this when verifying username and password
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # Set True if your broker supports TLS
lesson_topic = 'lessons_mqtt'
testing_topic = 'testing_mqtt'

mqtt_client = Mqtt(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for all domains

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully')
        mqtt_client.subscribe(lesson_topic)
        mqtt_client.subscribe(testing_topic)
    else:
        print('Bad connection. Code:', rc)

@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    with app.app_context():
        data = dict(
            topic=message.topic,
            payload=message.payload.decode()
        )
        print('Received message on topic: {topic} with payload: {payload}'.format(**data))
        socketio.emit('mqtt_data', data)  # Emit data to SocketIO clients

@socketio.on('publish_mqtt')
def handle_publish_mqtt(data):
    topic = data['topic']
    message = data['payload']
    mqtt_client.publish(topic, message)

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)
