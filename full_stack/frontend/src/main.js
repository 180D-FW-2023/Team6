import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createVuetify } from 'vuetify';
import 'vuetify/styles'; // Import Vuetify styles

// Create a new Vuetify instance (with any options you want)
const vuetify = createVuetify({});

// Create the Vue application instance
const app = createApp(App);

// Use the router and Vuetify instance with the Vue application
app.use(router);
app.use(vuetify);

// Mount the Vue application to the DOM
app.mount('#app');
