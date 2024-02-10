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
    result = db.scale.insert_one(content)
    return jsonify({"message": "Document added", "document_id": str(result.inserted_id)})

@app.route('/get-chord', methods=['GET'])
def get_chord_details():
    # Get query parameters
    modality = request.args.get('modality', type=str)
    key = request.args.get('key', type=str)

    # Normalize the input to match the case sensitivity of the database entries
    modality = modality.lower().capitalize() if modality else modality  # Example: 'major' -> 'Major'
    key = key.upper() if key else key  # Example: 'a' -> 'A'

    # Construct the query
    query = {'modality': modality, 'key': key} if modality and key else {}

    document = db.chords.find_one(query)

    # Find the document
    if document:
            # Extract the fields
            results = document.get('results', [])
            last_score = document.get('last_score')
            overall_avg = document.get('overall_avg')
            
            # Prepare the response
            response = {
                'results': results,
                'last_score': last_score,
                'overall_avg': overall_avg
            }
            return jsonify(response)
    else:
        return jsonify({"error": "Document not found with the provided modality and key."}), 404
    
@app.route('/get-scale', methods=['GET'])
def get_scale_details():
    # Get query parameters
    modality = request.args.get('modality', type=str)
    key = request.args.get('key', type=str)

    # Normalize the input to match the case sensitivity of the database entries
    modality = modality.lower().capitalize() if modality else modality  # Example: 'major' -> 'Major'
    key = key.upper() if key else key  # Example: 'a' -> 'A'

    # Construct the query
    query = {'modality': modality, 'key': key} if modality and key else {}

    document = db.scales.find_one(query)

    # Find the document
    if document:
            # Extract the fields
            results = document.get('results', [])
            last_score = document.get('last_score')
            overall_avg = document.get('overall_avg')
            
            # Prepare the response
            response = {
                'results': results,
                'last_score': last_score,
                'overall_avg': overall_avg
            }
            return jsonify(response)
    else:
        return jsonify({"error": "Document not found with the provided modality and key."}), 404
    

@app.route('/update_chord', methods=['POST'])
def update_chord():
    # Extract the data from the request's body
    data = request.get_json()
    modality = data.get('modality', '').capitalize()
    key = data.get('key', '').upper()
    results = data.get('results')
    last_score = data.get('last_score')
    overall_avg = data.get('overall_avg')

    # Construct the query
    query = {'modality': modality, 'key': key}
    
    # Find the document
    document = db.chords.find_one(query)
    
    if document:
        # Document exists, so update it
        if results:
            db.chords.update_one(query, {'$push': {'results': results}})
        if last_score is not None:
            db.chords.update_one(query, {'$set': {'last_score': last_score}})
        if overall_avg is not None:
            db.chords.update_one(query, {'$set': {'overall_avg': overall_avg}})
        return jsonify({"message": "Document updated"}), 200
    else:
        # No document found, create a new one
        new_document = {
            'modality': modality,
            'key': key,
            'results': [results] if results else [],
            'last_score': last_score,
            'overall_avg': overall_avg
        }
        db.chords.insert_one(new_document)
        return jsonify({"message": "New document created"}), 201

    


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)
