<template>
  <v-app-bar app color="primary" dark>
    <v-toolbar-title>{{ appName }}</v-toolbar-title>
    <v-spacer></v-spacer>
    <v-menu offset-y>
      <template v-slot:activator="{ on, attrs }">
        <v-btn v-bind="attrs" v-on="on" :color="buttonColor" dark>
          <v-icon left>mdi-menu</v-icon>
          Apps de bienestar
        </v-btn>
      </template>
      <v-list>
        <v-list-item
          v-for="(description, name) in appList"
          :key="name"
          :href="`/?crew_name=${name}`"
          :disabled="name === currentCrewName"
        >
          <v-list-item-title>
            <strong>{{ name }}</strong>: {{ description }}
            <v-icon v-if="name === currentCrewName" color="primary">mdi-check-circle</v-icon>
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-app-bar>
</template>

<script>
import axios from 'axios';
import yaml from 'js-yaml';

export default {
  name: 'AppBar',
  props: {
    appName: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      appList: {},
      currentCrewName: this.$route.query.crew_name || '', // Obtener el nombre de la app actual desde la URL
      buttonColor: 'secondary' // Color por defecto del botón
    };
  },
  created() {
    this.loadGlobalConfig();
    this.checkCrewName();
  },
  methods: {
    /**
     * Load global configuration from the specified URL
     */
    async loadGlobalConfig() {
      try {
        const configPath = '/etc/configs/global-config.yaml';
        console.log(`Fetching global configuration from: ${configPath}`);

        const response = await axios.get(configPath);
        let configData = response.data;

        if (typeof configData === 'string') {
          configData = yaml.load(configData);
        }

        if (!configData?.app_list) {
          throw new Error('Invalid global configuration structure');
        }

        this.appList = configData.app_list;
        console.log('Loaded global configuration:', this.appList);
      } catch (error) {
        console.error('Error loading global configuration:', error);
      }
    },
    /**
     * Check if crew_name exists in the URL and alert the user if not
     */
    checkCrewName() {
      if (!this.currentCrewName) {
        alert('Please select an option from "Apps de bienestar".');
        this.buttonColor = 'red'; // Remarcar el botón en rojo
      }
    }
  }
}
</script>

<style scoped>
/* Añadir estilos específicos si es necesario */
</style>
