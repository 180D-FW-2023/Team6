<template>
    <v-app>
      <v-container>
  
        <!-- First Button Group: Chords and Scales -->
        <v-btn-toggle v-model="selectedOption" mandatory>
          <v-btn value="Chords">Chords</v-btn>
          <v-btn value="Scales">Scales</v-btn>
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

      <!-- Test Button -->
      <v-btn @click="openDialog('Test')">Test</v-btn>

      <!-- Learn Button -->
      <v-btn @click="openDialog('Learn')">Learn</v-btn>

      <!-- Dialog for Testing or Learning -->
      <v-dialog v-model="dialog" persistent max-width="300px">
        <v-card>
          <v-card-title class="headline">{{ selectedAction }}</v-card-title>
          <v-card-text>
            <div>{{ selectedLetter }} {{ selectedType }} {{ selectedOption }}</div>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="green darken-1" text @click="dialog = false">Close</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      </v-container>
    </v-app>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  import { VApp, VContainer, VBtn, VBtnToggle, VSelect, VDialog, VCard, VCardTitle, VCardText, VCardActions, VSpacer } from 'vuetify/components';
  const selectedOption = ref('Chords');
const selectedType = ref('Major');
const selectedLetter = ref('A');
const dialog = ref(false);
const selectedAction = ref('');

const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

const openDialog = (action) => {
  selectedAction.value = action;
  dialog.value = true;
};
  </script>
  
  <style scoped>
  /* Add your styles here */
  </style>
  