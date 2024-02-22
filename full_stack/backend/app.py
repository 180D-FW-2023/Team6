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

    


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)
