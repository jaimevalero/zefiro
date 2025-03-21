<template>
  <v-app>
    <AppBar :appName="appName" />
    <v-main class="main-content">
      <v-container class="pa-0">
        <v-row justify="center" no-gutters>
          <v-col cols="12" md="10" lg="10">
            <v-card class="mt-0">
              <!-- Pasar la configuración al componente MainInfo -->
              <MainInfo :config="config" />
              <v-divider class="my-4"></v-divider>
              <EntryForm
                :minWords="minWords"
                :dataPolicyAccepted="dataPolicyAccepted"
                @submit="submitForm"
                @update:dataPolicyAccepted="dataPolicyAccepted = $event"
              >
              </EntryForm>

              <v-snackbar v-model="generatingReportSnackbar" :timeout="3000" right>
                Generando informe...
              </v-snackbar>

              <ReportStatus v-if="reportStatusVisible" :status="reportStatus" :uuid="jobId" />
              <v-alert type="info" class="mt-4">
                API URL: {{ apiUrl }}
                <br>
                FORM DATA: {{ filteredFormData }}
              </v-alert>
              <v-alert v-if="errorMessage" type="error" class="mt-4">
                {{ errorMessage }}
              </v-alert>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
    <v-footer app color="primary" dark class="footer-compact" absolute>
      <v-col class="text-right py-2" cols="12">
        <v-btn icon href="https://github.com/jaimevalero/gifted-children-helper" target="_blank">
          <v-icon>mdi-github</v-icon>
        </v-btn>
        Hecho con <v-icon color="red">mdi-heart</v-icon>
      </v-col>
    </v-footer>
  </v-app>
</template>

<script>
import EntryForm from '~/components/EntryForm.vue';
import MainInfo from '~/components/MainInfo.vue';
import TermsAndPolicy from '~/components/TermsAndPolicy.vue';
import ReportStatus from '~/components/ReportStatus.vue';
import AppBar from '~/components/AppBar.vue'; // Importar el nuevo componente
import { generateUUID } from '~/utils.js';
import themeService from '~/services/theme-service.js';
import axios from 'axios';
import yaml from 'js-yaml';

export default {
  name: 'IndexPage',
  components: {
    EntryForm,
    MainInfo,
    TermsAndPolicy,
    ReportStatus,
    AppBar // Registrar el nuevo componente
  },
  data() {
    return {
      dataPolicyAccepted: false,
      minWords: 100,
      snackbar: false,
      generatingReportSnackbar: false,
      reportStatus: {},
      reportStatusVisible: false,
      retryCount: 0,
      maxRetries: 5,
      jobId: '',
      appName: '',
      config: null,
      configLoaded: false,
      configError: null,
      apiUrl: process.env.VUE_APP_API_URL,
      errorMessage: '',
      filteredFormData: {},
      themeColors: null, // To store theme colors
      themeLoaded: false // Flag to indicate theme loading status
    };
  },
  created() {
    const urlParams = new URLSearchParams(window.location.search);
    const crewName = urlParams.get('crew_name');
    if (crewName) {
      this.loadAppConfig(crewName);
    } else {
      console.warn('No crew_name specified in URL. App name cannot be displayed.');
    }
  },
  methods: {
    /**
     * Loads configuration for the specified crew name
     * @param {string} crewName - The name of the crew to load configuration for
     */
    async loadAppConfig(crewName) {
      try {
        // Use theme service to load config and apply theme
        const configData = await themeService.loadTheme(crewName, this.$vuetify);

        this.appName = configData.frontend.app_name || 'App Name';
        this.config = configData;
        this.configLoaded = true;
        this.themeLoaded = true;

        // Store theme colors for components that might need them
        if (configData.frontend && configData.frontend.theme && configData.frontend.theme.colors) {
          this.themeColors = configData.frontend.theme.colors;
        }

        console.log(`Loaded app config for crew: ${crewName}`);
      } catch (error) {
        console.error('Error loading app configuration:', error);
        this.configError = error.message;
        this.errorMessage = 'Error loading configuration. Please try again later.';
      }
    },

    onAcceptChange(accepted) {
      this.dataPolicyAccepted = accepted;
    },
    async submitForm(formData) {
      console.log('Form data:', formData);

      const jobId = generateUUID();
      this.jobId = jobId;
      console.log('Generated Job ID:', jobId);

      this.generatingReportSnackbar = true;

      try {
        const apiUrl = process.env.VUE_APP_API_URL;
        if (!apiUrl) {
          throw new Error('API URL is not defined in environment variables');
        }

        console.log('API URL:', apiUrl);

        const { totalWordCount, ...filteredFormData } = formData;
        this.filteredFormData = filteredFormData; // Update the property here

        const response = await fetch(`${apiUrl}/generate-report`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ uuid: jobId, ...filteredFormData })
        });

        if (!response.ok) {
          throw new Error('Failed to submit form');
        }

        const result = await response.json();
        console.log('Form submitted successfully:', result);
        this.snackbar = true;
        this.reportStatusVisible = true;
        this.reportStatus = { uuid: jobId, progress: 0 };
        this.pollReportStatus(jobId);

      } catch (error) {
        console.error('Error submitting form:', error);
        this.errorMessage = 'Error submitting form. Please try again later.';
      } finally {
        this.generatingReportSnackbar = false;
      }
    },
    async pollReportStatus(uuid) {
      try {
        const apiUrl = process.env.VUE_APP_API_URL;
        const response = await fetch(`${apiUrl}/report_status/${uuid}`);
        if (!response.ok) {
          throw new Error('Failed to fetch report status');
        }

        const status = await response.json();
        this.reportStatus = status;

        if (status.progress < 1) {
          setTimeout(() => this.pollReportStatus(uuid), 5000);
        } else {
          console.log('Report generation complete');
        }
      } catch (error) {
        console.error('Error fetching report status:', error);
        //this.errorMessage = 'Error fetching report status. Please try again later.';
      }
    }
  },
  // Add provide to make theme colors available to descendant components
  provide() {
    return {
      getThemeColors: () => this.themeColors,
      themeLoaded: () => this.themeLoaded
    };
  }
}
</script>

<style>
.main-content {
  padding-top: 0 !important;
}

.v-application--wrap {
  min-height: 100vh !important;
}

.v-app-bar + .v-main {
  padding-top: 64px !important;
}

@import 'https://cdn.jsdelivr.net/npm/vuetify@2.6.4/dist/vuetify.min.css';

.footer-compact {
  min-height: 40px !important;
  height: auto !important;
  position: fixed !important;
  bottom: 0 !important;
  width: 100% !important;
  z-index: 100 !important;
}

.footer-compact .v-btn {
  margin: 0 4px !important;
}

.v-application .v-footer:not(.footer-compact) {
  display: none !important;
}

.v-main {
  padding-bottom: 40px !important;
}
</style>
