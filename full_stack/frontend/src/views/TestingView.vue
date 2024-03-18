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

        <!-- Test Button -->
        <v-btn @click="openDialog('Test')">Test</v-btn>

        <!-- Learn Button -->
        <v-btn @click="openDialog('Learn')">Learn</v-btn>

        <!-- Dialog for Testing or Learning -->
        <v-dialog v-model="dialog" persistent max-width="300px">
          <v-card>
            <v-card-title class="headline">{{ selectedAction }}</v-card-title>
            <v-card-text>
              <div>
                {{ selectedLetter }} {{ selectedType }} {{ selectedOption }}
              </div>
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn color="green darken-1" text @click="dialog = false"
                >Close</v-btn
              >
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-container>
      <v-container>
        <div><h1>Statistics</h1></div>
        <v-card class="mb-4">
          <v-card-title class="text-h6">Last test results</v-card-title>
          <v-card-text>
            <div class="card-container">
              <v-card v-for="(value, index) in lastResult" :key="index"
                :class="{'item-style': true, 'text-green': lastCorrectIndices[index] === 1, 'text-red': lastCorrectIndices[index] === 0}"
                class="square-card"
                rounded="lg"
              >
                <v-card-text class="card-text text-center">{{ value }}</v-card-text>
              </v-card>
            </div>
          </v-card-text>
        </v-card>
        <v-row>
          <v-col cols="12" sm="6" md="5">
            <v-responsive :aspect-ratio="1">
              <v-card>
                Last bad posture detected: 
              <img src="http://localhost:5000//uploads/image.jpg" class="responsive-image">
            </v-card>
            </v-responsive>
          </v-col>
          <v-col cols="12" sm="6" md="5">
            <v-responsive :aspect-ratio="1">
              <Line :data="chartData" :options="chartOptions" :key="chartKey" class="chart" />
            </v-responsive>
          </v-col>
        </v-row>
      </v-container>


    </v-app>
  </template>

<script setup>
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { VRow, VCol } from "vuetify/components";
import { ref, onMounted, watch } from "vue";
import io from "socket.io-client";
import axios from "axios";
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
const dialog = ref(false);
const selectedAction = ref("");
const mqttData = ref(null);
const lastResult = ref([]);
const lastCorrectIndices = ref([]);
const socket = io("http://127.0.0.1:5000");
const chartKey = ref(0);
const chartData = ref({
  labels: [],
  datasets: [{
    label: 'Your Label',
    data: [],
    backgroundColor: 'rgba(54, 162, 235, 0.5)',
    borderColor: 'rgba(54, 162, 235, 1)',
    borderWidth: 1,
  }]
});

const chartOptions = ref({
  scales: {
    y: {
      beginAtZero: true,
      suggestedMax: 100, // Adjust according to your scoring system
    },
    x: {
      title: {
        display: true,
        text: 'Attempt Number'
      }
    }
  },
  plugins: {
    legend: {
      display: false, // Hide legend if not needed
    },
    title: {
      display: true,
      text: 'Scores Over Attempts'
    }
  }
});
const letters = ["A", "B", "C", "D", "E", "F", "G"];
// const scales = {
//   // Major Scales
//   "C Major": "C3 D3 E3 F3 G3 A3 B3 C4",
//   "D Major": "D3 E3 F#3 G3 A3 B3 C#4 D4",
//   "E Major": "E3 F#3 G#3 A3 B3 C#4 D#4 E4",
//   "F Major": "F3 G3 A3 A#3 C4 D4 E4 F4",
//   "G Major": "G3 A3 B3 C4 D4 E4 F#4 G4",
//   "A Major": "A3 B3 C#4 D4 E4 F#4 G#4 A4",
//   "B Major": "B3 C#4 D#4 E4 F#4 G#4 A#4 B4",

//   // Natural Minor Scales
//   "A Minor": "A3 B3 C4 D4 E4 F4 G4 A4",
//   "B Minor": "B3 C#4 D4 E4 F#4 G4 A4 B4",
//   "C Minor": "C3 D3 D#3 F3 G3 G#3 A#3 C4",
//   "D Minor": "D3 E3 F3 G3 A3 A#3 C4 D4",
//   "E Minor": "E3 F#3 G3 A3 B3 C4 D4 E4",
//   "F Minor": "F3 G3 G#3 A#3 C4 C#4 D#4 F4",
//   "G Minor": "G3 A3 A#3 C4 D4 D#4 F4 G4",
// };

const scales = {
  "C Major": "C3 D3 E3 F3 G3 A3 B3 C4",
  "D Major": "D3 E3 F#3 G3 A3 B3 C#4 D4",
  "E Major": "E3 F#3 G#3 A3 B3 C#4 D#4 E4",
  "F Major": "F3 G3 A3 A#3 C4 D4 E4 F4",
  "G Major": "G3 A3 B3 C4 D4 E4 F#4 G4",
  "A Major": "A2 B2 C#3 D3 E3 F#3 G#3 A3",
  "B Major": "B2 C#3 D#3 E3 F#3 G#3 A#3 B3",

  "A Minor": "A2 B2 C3 D3 E3 F3 G3 A3",
  "B Minor": "B2 C#3 D3 E3 F#3 G3 A3 B3",
  "C Minor": "C3 D3 D#3 F3 G3 G#3 A#3 C4",
  "D Minor": "D3 E3 F3 G3 A3 A#3 C4 D4",
  "E Minor": "E3 F#3 G3 A3 B3 C4 D4 E4",
  "F Minor": "F3 G3 G#3 A#3 C4 C#4 D#4 F4",
  "G Minor": "G3 A3 A#3 C4 D4 D#4 F4 G4",
}

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

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)
const updateChartData = (scores) => {
  console.log(scores);
  if (!scores || scores.length === 0) {
    // If scores is undefined or an empty array, clear the chart data
    chartData.value.labels = [];
    chartData.value.datasets[0].data = [];
  } else {
    // If scores has data, update the chart data as before
    chartData.value.labels = scores.map((_, index) => `Attempt ${index + 1}`);
    chartData.value.datasets[0].data = scores;
  }

  // This step is crucial for triggering reactivity when updating nested properties in Vue 3
  chartData.value = { ...chartData.value };
  chartKey.value++; // Increment the key to force re-render
};

const getStats = async (type, modality, key) => {
  let endpoint = "";
  if (type === "Chord") {
    endpoint = "get-chord";
  } else if (type === "Scale") {
    endpoint = "get-scale";
  }

  try {
    const response = await axios.get(`http://127.0.0.1:5000/${endpoint}`, {
      params: {
        modality: modality,
        key: key,
      },
    });
    // Assuming response.data.results is the string from which you want to extract the last element
    if (response.data && Array.isArray(response.data.results) && Array.isArray(response.data.correct_indices)) {
      lastResult.value = response.data.results[response.data.results.length - 1].split(' ');
      lastCorrectIndices.value = response.data.correct_indices
      console.log(response.data.results);
      console.log("last correct indices: ", lastCorrectIndices.value  );
    } else {
      lastResult.value = []; // Fallback message
    }
    updateChartData(response.data.scores);
  } catch (error) {
    console.error(error);
    lastResult.value = []; // Error message
    updateChartData([]);
  }
};

const selectedImageUrl = ref('');

const pollForNewImage = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/check_for_updates');
    if (response.data.imageUrl) {
      selectedImageUrl.value = response.data.imageUrl;
      console.log("Entered");
      console.log(selectedImageUrl.value);
    }
  } catch (error) {
    console.error('Error polling for new image:', error);
  }
};
const refreshBadPostureImage = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/get_latest_image');
    if (response.data.imageUrl) {
      selectedImageUrl.value = response.data.imageUrl;
      console.log("Refreshed bad posture image:", selectedImageUrl.value);
    }
  } catch (error) {
    console.error('Error refreshing bad posture image:', error);
  }
};

onMounted(() => {
  socket.on("mqtt_data", (data) => {
    mqttData.value = `Topic: ${data.topic}, Payload: ${data.payload}`;
  });
  getStats(
    selectedOption.value,
    selectedType.value.toLowerCase(),
    selectedLetter.value
  );
  socket.on("update", () => {
    getStats(
    selectedOption.value,
    selectedType.value.toLowerCase(),
    selectedLetter.value
  );
   refreshBadPostureImage();
    this.$forceUpdate();
  })
  const pollInterval = 2000; // Poll every 2 seconds
  setInterval(() => {
    pollForNewImage();
  }, pollInterval);
});

watch(
  [selectedOption, selectedType, selectedLetter],
  () => {
    getStats(
      selectedOption.value,
      selectedType.value.toLowerCase(),
      selectedLetter.value
    );
  },
  { immediate: true }
); // immediate: true ensures getStats runs on initial setup as well

const openDialog = (action) => {
  selectedAction.value = action;
  dialog.value = true;

  // Construct the message to send
  const messageType = selectedType.value + " " + selectedOption.value;
  const message = selectedLetter.value + " " + messageType;
  let key;
  let scale;

  if (message.includes("Chord")) {
    key = message.replace(" Chord", "");
    scale = chords[key];
  } else if (message.includes("Scale")) {
    key = message.replace(" Scale", "");
    scale = scales[key];
  }
  console.log(message);
  console.log(scale);

  // Determine the topic based on the action
  const topic = action === "Test" ? "team6/test" : "team6/lesson";
  // Emit the message on the socket
  
  socket.emit("publish_mqtt", { topic: topic, payload: scale, key: message});
};
</script>

<style scoped>
.text-green {
  color: green;
}

.text-red {
  color: red;
}

.item-style {
  display: inline-block; /* or 'inline', depending on your needs */
  margin-right: 10px; /* Adjust spacing between items as needed */
}

.image-container {
  width: 100%;
  height: 0;
  padding-bottom: 100%; /* Maintain a square aspect ratio */
  position: relative;
}

.responsive-image {
  width: 100%;
  height: 100%;
  object-fit: contain; /* Adjust as needed (e.g., 'cover', 'fill') */
}

.chart {
  width: 100%;
  height: 100%;
}


.card-container {
  display: flex;
  flex-wrap: nowrap;
  gap: 16px;
  margin-bottom: 16px;
  overflow-x: auto;
}

.square-card {
  flex: 0 0 60px;
  height: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.card-text {
  font-size: 24px;
  font-weight: bold;
}

.text-center {
  text-align: center;
}
</style>
