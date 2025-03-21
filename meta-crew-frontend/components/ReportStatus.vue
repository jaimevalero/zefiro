<template>
  <v-card>
    <v-card-title>
      {{ title || 'Generando el informe (tarda unos diez minutos)' }}
      <v-spacer></v-spacer>
      <v-btn icon @click="toggleLogVisibility">
        <v-icon>{{ showLog ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-progress-linear
        v-if="progress !== 1"
        indeterminate
        height="10"
      ></v-progress-linear>
      <div v-if="showLog" v-html="renderedLog"></div> <!-- Render the Markdown as HTML -->
    </v-card-text>
    <v-snackbar v-model="reportGeneratedSnackbar" :timeout="3000" color="success">
      ¡Informe generado con éxito!
    </v-snackbar>
    <v-card-actions class="justify-center">
      <v-btn
        v-if="progress === 1"
        color="primary"
        @click="downloadReport"
        class="download-button"
        elevation="2"
        :loading="downloading"
      >
        <v-icon left>mdi-download</v-icon>
        Descargar reporte
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { convertMarkdownToHtml } from '../utils/markdown.js'; // Import the function

export default {
  name: 'ReportStatus',
  props: {
    status: {
      type: Object,
      required: true
    },
    uuid: {
      type: String,
      required: true
    },
    idToken: { // Add idToken prop
      type: String,
      required: true
    }
  },
  data() {
    return {
      progress: 0.1, // Initialize progress to 0
      title: '',
      log: '',
      intervalId: null, // Add an interval ID to manage the polling
      error: null, // Add an error property to handle errors
      lastStatus: null, // Add a property to store the last status
      reportGeneratedSnackbar: false, // Add a property for the snackbar
      showLog: true // Add a property to control log visibility
    };
  },
  computed: {
    renderedLog() {
      // Convert the Markdown log to HTML using the imported function
      return convertMarkdownToHtml(this.log);
    }
  },
  watch: {
    status(newStatus) {
      this.updateStatus(newStatus);
    },
    uuid: {
      immediate: true,
      handler(newUuid) {
        if (newUuid) {
          this.fetchReportStatus(newUuid);
        }
      }
    }
  },
  methods: {
    toggleLogVisibility() {
      this.showLog = !this.showLog;
    },
    updateStatus(newStatus) {
      console.log('Updating status:', newStatus);
      // Update the progress, title, and log based on the new status
      if (JSON.stringify(newStatus) !== JSON.stringify(this.lastStatus)) {
        if (newStatus.progress !== undefined) {
          console.log('Progress new value:', newStatus.progress);
          this.progress = Math.max(0, Math.min(newStatus.progress, 1)); // Ensure progress is between 0 and 1
          console.log('Progress new value changed', this.progress);

          // Mostrar el snackbar solo cuando el progreso llegue a 1
          if (newStatus.progress === 1) {
            this.reportGeneratedSnackbar = true;
            console.log('Report generation complete - showing snackbar');
            this.showLog = false; // Hide the log when progress reaches 1
          }
        }
        this.title = newStatus.title || '';
        let logEntry = newStatus.log || '';
        if (!logEntry.endsWith('\n')) {
          logEntry += '\n'; // Ensure the log entry ends with a newline
        }
        this.log += logEntry; // Add the new log entry
        this.lastStatus = newStatus; // Update the last status
      }
      console.log('Status updated:', newStatus);

      // Show snackbar and enable download button when progress reaches 1
      if (this.progress === 1) {
        this.reportGeneratedSnackbar = true;
      }
    },
    updateProgressBar(progress) {
      console.log("Actualizando el progreso");
      try {
        console.log(progress);
        // get current value, if not defined, set to 0
        let current_progress = this.progress || 0;
        let new_progress = Math.max(0, Math.min(progress, 1)); // Ensure progress is between 0 and 1

        if (progress < 0 || progress > 1) {
          throw new Error('Progress must be between 0 and 1');
        }
        this.progress = new_progress;
      } catch (error) {
        console.error('Error updating progress:', error);
        this.error = error.message;
        return;
      }
    },
    async pollStatus() {
      try {
        const apiUrl = process.env.VUE_APP_API_URL;
        if (!apiUrl) {
          throw new Error('API URL is not defined in environment variables');
        }
        console.log('Polling status...');
        const response = await fetch(`${apiUrl}/report_status/${this.uuid}`, {
          headers: {
            'Authorization': `Bearer ${this.idToken}` // Send the ID token in the Authorization header
          }
        });
        if (!response.ok) {
          console.error('Failed to fetch report status');
          throw new Error('Failed to fetch report status');
        }
        const data = await response.json();
        console.log(data);
        this.updateStatus(data);
        if (data.progress === 1) {
          console.log('Progress is 1');
          clearInterval(this.intervalId); // Stop polling when progress reaches 1
        }
      } catch (error) {
        console.error('Error fetching report status. Please try again later.');
        //this.error = 'Error fetching report status. Please try again later.';
      }
    },
    async fetchReportStatus(uuid) {
      try {
        const apiUrl = process.env.VUE_APP_API_URL;
        console.log('Fetching report status...');
        const response = await fetch(`${apiUrl}/report_status/${uuid}`, {
          headers: {
            'Authorization': `Bearer ${this.idToken}` // Send the ID token in the Authorization header
          }
        });
        if (!response.ok) {
          throw new Error('Failed to fetch report status');
        }
        const status = await response.json();
        console.log(status);
        this.$emit('update:status', status); // Emit the updated status to the parent component
      } catch (error) {
        console.error('Error fetching report status:', error);
        //this.error = 'Error fetching report status. Please try again later.';
      }
    },
    async downloadReport() {
      try {
        const apiUrl = process.env.VUE_APP_API_URL;
        const response = await fetch(`${apiUrl}/report_download/${this.uuid}`, {
          headers: {
            'Authorization': `Bearer ${this.idToken}` // Send the ID token in the Authorization header
          }
        });

        if (!response.ok) {
          throw new Error('Failed to download report');
        }

        const contentType = response.headers.get('Content-Type');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        // Determine the filename based on the content type
        if (contentType === 'text/markdown') {
          a.download = 'final_report.md';
        } else {
          a.download = 'final_report.pdf';
        }

        document.body.appendChild(a);
        a.click();
        a.remove();
      } catch (error) {
        console.error('Error downloading report:', error);
        this.error = 'Error downloading report. Please try again later.';
      }
    }
  },
  mounted() {
    this.progress = 0.5; // Set initial progress to 0.5
    this.updateProgressBar(this.progress); // Update the progress bar with the initial value
    this.intervalId = setInterval(this.pollStatus, 3000); // Start polling every 3 seconds
  },
  beforeDestroy() {
    clearInterval(this.intervalId); // Clear the interval when the component is destroyed
  }
}
</script>

<style scoped>
.v-card {
  margin-top: 20px;
}

.justify-center {
  display: flex;
  justify-content: center;
}

.download-button {
  border: 2px solid currentColor;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
  min-width: 200px;
}

.download-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.download-button:active {
  transform: translateY(0);
}
</style>

