<template>
    <div id="app">
        <h1>Lessons Page</h1>
      <div v-if="mqttData">
        <h2>Received MQTT Data:</h2>
        <pre>{{ mqttData }}</pre>
      </div>
      <div v-else>
        <p>No data received yet...</p>
      </div>
  
      <button @click="toggleLessonsDropdown">
        Lessons
      </button>
  
      <div v-if="lessonsDropdown">
        <button @click="selectLesson('A')">A</button>
        <button @click="selectLesson('B')">B</button>
        <button @click="selectLesson('C')">C</button>
        <button @click="selectLesson('F Major')">F Major</button>
      </div>
    </div>

    <h2>Statistics</h2>
  </template>
  
  <script>
  import { ref, onMounted } from 'vue';
  import io from 'socket.io-client';
  
  export default {
    setup() {
      const mqttData = ref(null);
      const lessonsDropdown = ref(false);
      const socket = io('http://127.0.0.1:5000');
  
      const lessons = {
        'A': 'aaaaa',
        'B': 'bbbbb',
        'C': 'C4 D4 E4 F4 G4 A4 B4 C5',
        'F Major': 'F3 G3 A3 A#3 C4 D4 E4 F4'
      };
  
      onMounted(() => {
        socket.on('mqtt_data', (data) => {
          mqttData.value = `Topic: ${data.topic}, Payload: ${data.payload}`;
        });
      });
  
      const toggleLessonsDropdown = () => {
        lessonsDropdown.value = !lessonsDropdown.value;
      };
  
      const selectLesson = (lessonKey) => {
        const lessonValue = lessons[lessonKey];
        socket.emit('publish_mqtt', { topic: 'team6/test', payload: lessonValue });
        console.log(`Selected lesson: ${lessonKey} - ${lessonValue}`);
        lessonsDropdown.value = false; // Optionally close the dropdown after a selection
      };
  
  
      return { mqttData, lessonsDropdown, toggleLessonsDropdown, selectLesson };
    }
  };
  </script>
  
  <style>
  /* Add your styles here */
  </style>