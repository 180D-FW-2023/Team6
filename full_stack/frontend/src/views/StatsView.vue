<template>
  <v-app>
    <v-container>
      <!-- First Button Group: Chords and Scales -->
      <v-btn-toggle v-model="selectedOption" mandatory>
        <v-btn value="Chord">Chords</v-btn>
        <v-btn value="Scale">Scales</v-btn>
      </v-btn-toggle>

      <!-- Second Button Group: Major and Minor -->
      <v-btn-toggle v-model="selectedType" mandatory>
        <v-btn value="Major">Major</v-btn>
        <v-btn value="Minor">Minor</v-btn>
      </v-btn-toggle>

      <!-- Slider for A to F -->
      <!-- Slider for A to F -->
      <v-select
        v-model="selectedLetter"
        :items="letters"
        label="Select Letter"
        outlined
      ></v-select>
    </v-container>
    <v-container>
      <div><h1>Statistics</h1></div>
      <div v-if="chordInfo">{{ chordInfo }}</div>
      <div v-else>Loading chord information...</div>
    </v-container>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from "vue";
import io from "socket.io-client";
import axios from 'axios';
import {
  VApp,
  VContainer,
  VBtn,
  VBtnToggle,
  VSelect,
  VDialog,
  VCard,
  VCardTitle,
  VCardText,
  VCardActions,
  VSpacer,
} from "vuetify/components";
const selectedOption = ref("Chord");
const selectedType = ref("Major");
const selectedLetter = ref("A");
const mqttData = ref(null);
const socket = io("http://127.0.0.1:5000");
const chordInfo = ref('');
const letters = ["A", "B", "C", "D", "E", "F", "G"];
const scales = {
  // Major Scales
  "C Major": "C4 D4 E4 F4 G4 A4 B4 C5",
  "D Major": "D3 E3 F#3 G3 A3 B3 C#4 D4",
  "E Major": "E3 F#3 G#3 A3 B3 C#4 D#4 E4",
  "F Major": "F3 G3 A3 A#3 C4 D4 E4 F4",
  "G Major": "G3 A3 B3 C4 D4 E4 F#4 G4",
  "A Major": "A3 B3 C#4 D4 E4 F#4 G#4 A4",
  "B Major": "B3 C#4 D#4 E4 F#4 G#4 A#4 B4",

  // Natural Minor Scales
  "A Minor": "A3 B3 C4 D4 E4 F4 G4 A4",
  "B Minor": "B3 C#4 D4 E4 F#4 G4 A4 B4",
  "C Minor": "C3 D3 D#3 F3 G3 G#3 A#3 C4",
  "D Minor": "D3 E3 F3 G3 A3 A#3 C4 D4",
  "E Minor": "E3 F#3 G3 A3 B3 C4 D4 E4",
  "F Minor": "F3 G3 G#3 A#3 C4 C#4 D#4 F4",
  "G Minor": "G3 A3 A#3 C4 D4 D#4 F4 G4",
};

const chords = {
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
};

const getChord = async (modality, key) => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/get-chord', {
      params: {
        modality: modality,
        key: key
      }
    });
    chordInfo.value = JSON.stringify(response.data); // Update chordInfo with the response data
  } catch (error) {
    console.error(error);
    chordInfo.value = 'Failed to load chord information'; // Update chordInfo on error
  }
};

onMounted(() => {
  socket.on("mqtt_data", (data) => {
    mqttData.value = `Topic: ${data.topic}, Payload: ${data.payload}`;
  });
  getChord(selectedType.value.toLowerCase(), selectedLetter.value); // Adjusted to use selectedType and selectedLetter
});

</script>

<style scoped>

</style>

