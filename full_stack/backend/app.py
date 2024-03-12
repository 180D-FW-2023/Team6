from flask import Flask, request, jsonify, send_from_directory
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_cors import CORS
import cv2
import time
import math as m
import mediapipe as mp
import time
import paho.mqtt.client as mqtt
import numpy as np
import os
import subprocess
import string
import signal
import sys
import inspect
import logging


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
last_sent_test_msg = "Last Sent Test Message Initialized"
script_process = None

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

process = None

def start_script():
    global process
    script_path = "C:/Users/danie/Documents/ECE 180/Team6/full_stack/backend/posture_detection.py"
    python_executable = sys.executable
    process = subprocess.Popen([python_executable, script_path])
    print("Script started with PID:", process.pid)

def stop_script():
    global process
    if process:
        os.kill(process.pid, signal.SIGTERM)
        process.wait()
        print("Script stopped.")
    else:
        print("No script is currently running.")

    

def remove_numbers(text):
    # Create a translation table that maps digits to None
    remove_digits = str.maketrans('', '', string.digits)
    
    # Use the translation table to remove digits from the string
    result = text.translate(remove_digits)
    
    return result


def process_test_result(payload):
    global last_sent_test_msg
    print('last sent test_msg:', last_sent_test_msg)
    print('payload: ', payload)
    dict_key = ' '.join(last_sent_test_msg[:7].split())
    words = last_sent_test_msg.split(" ")
    modality = words[1]
    correct_notes = []
    type = ""
    if 'Scale' in last_sent_test_msg:
        type = 'scales'
        correct_notes = scales[dict_key].replace('*', '#').split()
    elif 'Chord' in last_sent_test_msg:
        type = 'chords'
        correct_notes = chords[dict_key].replace('*', '#').split()
    payload_notes = payload.split()
    matching_indices = [i for i, item in enumerate(correct_notes) if i < len(payload_notes) and item == payload_notes[i]]
    boolean_indices = [0] * len(payload.split())
    for i in range(len(boolean_indices)):
        if i in matching_indices:
            boolean_indices[i] = 1
    score = (len(matching_indices) / len(correct_notes)) * 100
    print("Score: ", score)
    update_record_in_db(last_sent_test_msg[0], type, modality, remove_numbers(payload)[:-1], score, boolean_indices)
    print(matching_indices)
    print(correct_notes)
    socketio.emit('update')
    stop_script()
    return matching_indices


    print(f"Processing message from testing_topic: {payload}")

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
        if message.topic == testing_topic:
            process_test_result(data['payload'])
        socketio.emit('mqtt_data', data)  # Emit data to SocketIO clients


@socketio.on('publish_mqtt')
def handle_publish_mqtt(data):
    global last_sent_test_msg
    topic = data['topic']
    message = data['payload']
    if topic == 'team6/test':
        last_sent_test_msg = data['key']
        start_script()
        print("Last sent test msg:", last_sent_test_msg)
    mqtt_client.publish(topic, message)
    print("publishing", topic, message)



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

    

def update_record_in_db(key, type_, modality, new_result, new_score, correct_indices):
    print("updating record")
    collection = db[type_.lower()]
    update_response = collection.update_one(
        {'key': key, 'modality': modality},
        {
            '$push': {'results': new_result, 'scores': new_score},
            '$set': {'correct_indices': correct_indices},
            '$inc': {'attempts': 1}
        },
        upsert=True
    )
    return update_response


    
def check_result(type, test, result):
    if type == 'chord':
        pass
    elif type == 'scale':
        pass
    return

from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['BASE_URL'] = 'http://localhost:5000/'
latest_image_url = None

@app.route('/upload_frame', methods=['POST'])
def upload():
    global latest_image_url
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    
    file = request.files['image']
    print(request.form['text'])
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    # Change the file extension to .jpg to ensure the file is saved as a JPEG
    filename_jpeg = os.path.splitext(filename)[0] + '.jpg'
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename_jpeg)
    
    # Convert and save the image as a JPEG
    image = Image.open(file.stream)
    draw = ImageDraw.Draw(image)

    # Define the text properties
    font = ImageFont.truetype("arial.ttf", 20)  # You may need to adjust the font path
    text = request.form['text']
    text_position = (50, 50)
    text_color = "red"

    draw.text(text_position, text, fill=text_color, font=font)
    image.save(file_path, 'JPEG')
    latest_image_url = f"{app.config['BASE_URL']}/uploads/{filename_jpeg}"
    
    return jsonify({'message': 'Image received successfully'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/check_for_updates')
def check_for_updates():
    if latest_image_url:
        return jsonify({'imageUrl': latest_image_url}), 200
    else:
        return jsonify({'imageUrl': None}), 200
    
if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)
