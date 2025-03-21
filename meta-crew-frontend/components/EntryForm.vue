<template>
  <v-form @submit.prevent="handleSubmit">
    <v-divider class="my-4"></v-divider>
    <v-card-title class="text-h5">{{ formTitle || 'Formulario de entrada' }}</v-card-title>
    <p v-if="formDescription" class="px-4">{{ formDescription }}</p>

    <v-container>
      <v-row dense>
        <v-col cols="12" v-for="(field, index) in formFields" :key="index">
          <v-textarea
            outlined
            :label="field.label"
            v-model="formData[field.name]"
            rows="6"
            :placeholder="field.description"
            :prepend-inner-icon="getIconName(field.icon)"
            :required="field.required"
          />
        </v-col>

        <v-col cols="12">
          <p v-if="totalWordCount < minWords" class="error--text">Por favor debe rellenar al menos {{ minWords }} palabras. Palabras actuales: {{ totalWordCount }}</p>
        </v-col>
        <v-col cols="12">
          <TermsAndPolicy @accept-change="onAcceptChange" :defaultChecked="false" />
          <p v-if="!dataPolicyAccepted" class="error--text">
            Debes aceptar los términos de servicio.
          </p>
        </v-col>
        <v-col cols="12" class="text-right">
          <v-btn
            ref="submitButton"
            :disabled="totalWordCount < minWords || !dataPolicyAccepted || isLoading"
            :color="submitButtonColor"
            type="submit"
            @click="scrollToBottom"
          >
            <v-icon left>mdi-send</v-icon>
            Enviar
          </v-btn>
        </v-col>
        <v-snackbar v-model="loginSuccessSnackbar" :timeout="3000" right>
          ¡Usuario logado con éxito!
        </v-snackbar>
        <v-snackbar v-model="loadingErrorSnackbar" :timeout="5000" color="error" right>
          {{ loadingError }}
        </v-snackbar>
      </v-row>
    </v-container>
  </v-form>
</template>

<script>
import TermsAndPolicy from './TermsAndPolicy.vue';
import Cookies from 'js-cookie'; // Import js-cookie for handling cookies
import axios from 'axios'; // Import axios for HTTP requests
import yaml from 'js-yaml'; // Import js-yaml for parsing YAML

export default {
  name: 'EntryForm',
  components: {
    TermsAndPolicy // Register the component
  },
  // Inject theme colors from parent component
  inject: {
    getThemeColors: {
      default: () => ({})
    },
    themeLoaded: {
      default: () => false
    }
  },
  props: {
    dataPolicyAccepted: {
      type: Boolean,
      required: true,
      default: process.env.NODE_ENV === 'development' // Default to true in development
    }
  },
  data() {
    return {
      // Dynamic form data
      formData: {},
      formFields: [],
      formTitle: '',
      formDescription: '',

      minWords: 0,
      loginSuccessSnackbar: false,

      // Loading control properties
      isLoading: false,
      loadingError: '',
      loadingErrorSnackbar: false,
      crewName: null
    }
  },
  computed: {
    totalWordCount() {
      // Calculate word count from dynamic fields
      let wordCount = 0;

      // Count words in all form fields
      for (const fieldName in this.formData) {
        if (this.formData[fieldName]) {
          wordCount += this.formData[fieldName].split(' ').filter(word => word).length;
        }
      }

      return wordCount;
    },
    /**
     * Get theme-aware color for submit button
     * @returns {string} - Color name for submit button
     */
    submitButtonColor() {
      const themeColors = this.getThemeColors();
      return (themeColors && themeColors.success) ? 'success' : 'green';
    }
  },
  created() {
    this.loadFormConfigFromUrl();
  },
  methods: {
    /**
     * Load form configuration based on crew_name URL parameter
     * This method fetches and parses the YAML config file
     */
    async loadFormConfigFromUrl() {
      // Get crew_name from URL query parameters
      this.crewName = this.$route.query.crew_name;

      if (!this.crewName) {
        console.warn('No crew_name specified in URL. Form cannot be displayed.');
        this.loadingError = 'No se ha especificado un tipo de formulario. Por favor, añada el parámetro crew_name en la URL.';
        this.loadingErrorSnackbar = true;
        return;
      }

      this.isLoading = true;

      try {
        // Use the static path to get the configuration
        const configPath = `/etc/configs/${this.crewName}/config/config.yaml`;
        console.log(`Fetching configuration from: ${configPath}`);

        // Load the config file using axios
        const response = await axios.get(configPath);
        let configData = response.data;

        // If the response is a string (raw YAML), parse it
        if (typeof configData === 'string') {
          configData = yaml.load(configData);
        }

        if (!configData?.frontend?.form) {
          throw new Error('Invalid form configuration structure');
        }

        // Set form title and description
        this.formTitle = configData.frontend.form.title || 'Formulario de entrada';
        this.formDescription = configData.frontend.form.description || '';

        // Set form fields
        this.formFields = configData.frontend.form.fields || [];

        if (this.formFields.length === 0) {
          throw new Error('No form fields found in configuration');
        }

        // Initialize formData object with empty values for each field
        this.formFields.forEach(field => {
          this.formData[field.name] = '';
        });

        console.log(`Loaded ${this.formFields.length} form fields for crew: ${this.crewName}`);
      } catch (error) {
        console.error('Error loading form configuration:', error);
        this.loadingError = `Error al cargar la configuración del formulario: ${error.message}`;
        this.loadingErrorSnackbar = true;
      } finally {
        this.isLoading = false;
      }
    },
    /**
     * Maps icon names from config to mdi icon names
     * @param {String} iconName - Basic icon name from config
     * @return {String} Full mdi icon name
     */
    getIconName(iconName) {
      // Map of basic icon names to mdi icon names
      const iconMap = {
        'user': 'mdi-account',
        'stethoscope': 'mdi-stethoscope',
        'file-medical': 'mdi-file-document-outline',
        'pills': 'mdi-pill',
        'allergies': 'mdi-alert-circle',
        'users': 'mdi-account-group',
        'child': 'mdi-account-child',
        'baby': 'mdi-baby-face'
      };

      // Return mapped icon name or default icon if not found
      return iconMap[iconName] || `mdi-${iconName}` || 'mdi-text-box';
    },
    async handleSubmit() {
      try {
        if (this.totalWordCount < this.minWords) {
          console.error(`Minimum ${this.minWords} words required. Current: ${this.totalWordCount}`);
          return;
        }

        // Prepare data to submit
        const dataToSubmit = {
          ...this.formData,
          totalWordCount: this.totalWordCount,
          crew_name: this.crewName
        };

        // Emit form data to parent component
        this.$emit('submit', dataToSubmit);

        // Scroll to the bottom of the page after form submission
        this.scrollToBottom();
      } catch (error) {
        console.error('Submit failed:', error);
        this.$emit('error', 'Error al enviar el formulario.');
        return;
      }
    },
    scrollToBottom() {
      // Ensure the ref is correctly accessed
      const submitButton = this.$refs.submitButton.$el;
      if (submitButton && typeof submitButton.scrollIntoView === 'function') {
        submitButton.scrollIntoView({ behavior: 'smooth', block: 'end' });
      } else {
        console.error('submitButton ref is not correctly defined or scrollIntoView is not a function');
      }
    },
    onAcceptChange(accepted) {
      this.$emit('update:dataPolicyAccepted', accepted);
      if (accepted) {
        this.warmupBackend();
      }
    },
    async warmupBackend() {
      console.log('Initiating backend warmup...');  // Añadimos log para debug
      const apiUrl = process.env.VUE_APP_API_URL;
      if (!apiUrl) {
        console.warn('API URL is not defined in environment variables');
        return;
      }

      const checkHealth = async () => {
        try {
          const response = await fetch(`${apiUrl}/health`);
          if (response.ok) {
            console.debug('Backend is awake');
          } else {
            throw new Error('Backend is not ready');
          }
        } catch (error) {
          console.debug('Retrying warmup request in 3 seconds');
          setTimeout(checkHealth, 3000); // Retry after 3 seconds
        }
      };

      // Start the initial health check
      checkHealth();
    }
  },
  errorCaptured(err, vm, info) {
    console.error('Error captured in EntryForm:', err, info);
    this.loadingError = `Error in EntryForm: ${err.message}`;
    this.loadingErrorSnackbar = true;
    return false; // Prevent the error from propagating further
  }
}
</script>

<style scoped>
</style>
