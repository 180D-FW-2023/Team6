<template>
  <div id="app">
    <h1>MQTT Data Display</h1>
    <div v-if="mqttData">
      <h2>Received MQTT Data:</h2>
      <pre>{{ mqttData }}</pre>
    </div>
    <div v-else>
      <p>No data received yet...</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import io from 'socket.io-client';

export default {
  setup() {
    const mqttData = ref(null);
    const socket = io('http://127.0.0.1:5000');

    onMounted(() => {
      socket.on('mqtt_data', (data) => {
        mqttData.value = `Topic: ${data.topic}, Payload: ${data.payload}`;
      });
    });

    return { mqttData };
  }
};
</script>

<style>
/* Add your styles here */
</style>
