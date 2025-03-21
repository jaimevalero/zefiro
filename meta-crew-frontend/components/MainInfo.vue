<template>
  <div class="main-info">
    <v-alert :color="secondaryColor" type="info" class="mb-2 mt-0">
      {{ config?.frontend?.main_info || 'Loading...' }}
      <br><br>
      Por favor, completa el formulario de entrada para generar un informe personalizado. (Tarda unos 10 minutos)
      <v-btn :href="config?.frontend?.download_example_report_link || '#'" target="_blank" :color="accentColor" class="mt-2">
        <v-icon left>mdi-download</v-icon>
        Descargar reporte de ejemplo ficticio
      </v-btn>
    </v-alert>
    <v-alert :color="secondaryColor" type="info" class="mt-2">
      No olvides aceptar los términos del servicio.
    </v-alert>
  </div>
</template>

<script>
import { logColorSelection } from '../utils/logging.js';

export default {
  name: 'MainInfo',
  inject: {
    getThemeColors: {
      default: () => ({})
    },
    themeLoaded: {
      default: () => false
    }
  },
  props: {
    config: {
      type: Object,
      default: () => null
    }
  },
  computed: {
    /**
     * Get primary color from theme or fallback to default
     * Following the Fail Fast principle by validating theme data
     * @returns {string} CSS color value
     */
    primaryColor() {
      const themeColors = this.getThemeColors() || {}; // Ensure object even if null/undefined
      const color = themeColors.primary;

      // Log color selection for debugging purposes
      logColorSelection('primary', color, !!color);

      return color || 'primary'; // Fallback to Vuetify's named color
    },

    /**
     * Get secondary color from theme or fallback to default
     * @returns {string} CSS color value
     */
    secondaryColor() {
      const themeColors = this.getThemeColors() || {};
      const color = themeColors.secondary;

      // Log color selection for debugging purposes
      logColorSelection('secondary', color, !!color);

      return color || 'secondary';
    },

    /**
     * Get accent color from theme or fallback to default
     * Provides visual contrast for interactive elements like buttons
     * @returns {string} CSS color value
     */
    accentColor() {
      const themeColors = this.getThemeColors() || {};
      const color = themeColors.accent;

      // Log color selection for debugging purposes
      logColorSelection('accent', color, !!color);

      return color || 'accent'; // Fallback to Vuetify's named color
    }
  },
  mounted() {
    // Simple validation of theme data
    if (!this.getThemeColors()) {
      console.warn('No theme colors provided to MainInfo component');
    }
  }
}
</script>

<style scoped>
.main-info {
  padding-top: 0;
}

.v-alert {
  margin-bottom: 8px !important;
}
</style>
