<template>
  <v-app>
    <v-app-bar app>
      <v-toolbar-title>Virtual Piano Teacher</v-toolbar-title>

      <v-spacer></v-spacer>

      <v-btn text to="/">Home</v-btn>
      <v-btn text to="/stats">Stats</v-btn>
      <v-btn text to="/testing">Testing</v-btn>
    </v-app-bar>

    <v-main>
      <RouterView />
    </v-main>
  </v-app>
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router';
import { VApp, VAppBar, VToolbarTitle, VSpacer, VBtn, VMain } from 'vuetify/components';

import HelloWorld from './components/HelloWorld.vue';
</script>

<style scoped>
/* Add any additional styling here */
</style>
