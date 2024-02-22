from flask import Flask, request, jsonify
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_cors import CORS


from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://team6:mongodb@pianoteacher.wwyj7r1.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.Team6

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__)
CORS(app)

app.config['MQTT_BROKER_URL'] = 'test.mosquitto.org'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''  # Set this when verifying username and password
app.config['MQTT_PASSWORD'] = ''  # Set this when verifying username and password
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # Set True if your broker supports TLS
lesson_topic = 'team6/lessons/results'
testing_topic = 'team6/test/results'

scales = {
  "C Major": "C3 D3 E3 F3 G3 A3 B3 C4",
  "D Major": "D3 E3 F#3 G3 A3 B3 C#4 D4",
  "E Major": "E3 F#3 G#3 A3 B3 C#4 D#4 E4",
  "F Major": "F3 G3 A3 A#3 C4 D4 E4 F4",
  "G Major": "G3 A3 B3 C4 D4 E4 F#4 G4",
  "A Major": "A3 B3 C#4 D4 E4 F#4 G#4 A4",
  "B Major": "B3 C#4 D#4 E4 F#4 G#4 A#4 B4",

  "A Minor": "A3 B3 C4 D4 E4 F4 G4 A4",
  "B Minor": "B3 C#4 D4 E4 F#4 G4 A4 B4",
  "C Minor": "C3 D3 D#3 F3 G3 G#3 A#3 C4",
  "D Minor": "D3 E3 F3 G3 A3 A#3 C4 D4",
  "E Minor": "E3 F#3 G3 A3 B3 C4 D4 E4",
  "F Minor": "F3 G3 G#3 A#3 C4 C#4 D#4 F4",
  "G Minor": "G3 A3 A#3 C4 D4 D#4 F4 G4",
}

chords = {
  "C Major": "C3 E3 G3",
  "C Minor": "C3 D#3 G3",
  "D Major": "D3 F#3 A3",
  "D Minor": "D3 F3 A3",
  "E Major": "E3 G#3 B3",
  "E Minor": "E3 G3 B3",
  "F Major": "F3 A3 C4",
  "F Minor": "F3 G#3 C4",
  "G Major": "G3 B3 D4",
  "G Minor": "G3 A#3 D4",
  "A Major": "A3 C#4 E4",
  "A Minor": "A3 C4 E4",
  "B Major": "B3 D#4 F#4",
  "B Minor": "B3 D4 F#4",
}

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

@app.route('/add-chord', methods=['POST'])
def add_chord():
    content = request.json
    result = db.chords.insert_one(content)
    return jsonify({"message": "Document added", "document_id": str(result.inserted_id)})

@app.route('/add-scale', methods=['POST'])
def add_scale():
    content = request.json
    result = db.scales.insert_one(content)
    return jsonify({"message": "Document added", "document_id": str(result.inserted_id)})

from bson import ObjectId

# Helper function to convert ObjectId to string
def serialize_document(document):
    if document and "_id" in document:
        document["_id"] = str(document["_id"])
    return document

@app.route('/get-chord', methods=['GET'])
def get_chord_details():
    modality = request.args.get('modality', type=str)
    key = request.args.get('key', type=str)
    modality = modality.lower().capitalize() if modality else modality
    key = key.upper() if key else key
    query = {'modality': modality, 'key': key} if modality and key else {}
    document = db.chords.find_one(query)
    if document:
        document["_id"] = str(document["_id"])  # Serialize ObjectId to string
        return jsonify(document)
    else:
        return jsonify({"error": "Document not found with the provided modality and key."}), 404


@app.route('/get-scale', methods=['GET'])
def get_scale_details():
    modality = request.args.get('modality', type=str)
    key = request.args.get('key', type=str)
    modality = modality.lower().capitalize() if modality else modality
    key = key.upper() if key else key
    query = {'modality': modality, 'key': key} if modality and key else {}
    document = db.scales.find_one(query)
    if document:
        document["_id"] = str(document["_id"])  # Serialize ObjectId to string
        return jsonify(document)
    else:
        return jsonify({"error": "Document not found with the provided modality and key."}), 404

    

@app.route('/update_chord', methods=['POST'])
def update_chord():
    data = request.get_json()
    modality = data.get('modality', '').capitalize()
    key = data.get('key', '').upper()

    # Construct the query
    query = {'modality': modality, 'key': key}
    
    update_data = {}
    if 'results' in data:
        update_data['$push'] = {'results': {'$each': data['results']}}
    if 'scores' in data:
        update_data.setdefault('$push', {})['scores'] = {'$each': data['scores']}
    if 'mistake_count' in data:
        update_data.setdefault('$push', {})['mistake_count'] = {'$each': data['mistake_count']}
    if 'attempts' in data:
        update_data['$inc'] = {'attempts': data['attempts']}

    result = db.chords.update_one(query, update_data)

    if result.matched_count:
        return jsonify({"message": "Document updated"}), 200
    else:
        # If no document matches the query, create a new document
        new_document = data
        db.chords.insert_one(new_document)
        return jsonify({"message": "New document created"}), 201

    
def check_result(type, test, result):
    if type == 'chord':
        pass
    elif type == 'scale':
        pass
    return

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)
