import axios from 'axios';
import yaml from 'js-yaml';

/**
 * Theme service to centralize theming logic across the application
 * Following the Single Responsibility Principle by having a dedicated service for theme management
 */
export default {
  /**
   * Load configuration and extract theme settings
   * @param {string} crewName - The crew name used to locate configuration
   * @param {Object} vuetify - The Vuetify instance to apply theme to
   * @returns {Promise<Object>} - The loaded configuration
   */
  async loadTheme(crewName, vuetify) {
    try {
      // Get configuration from the specified crew
      const configPath = `/etc/configs/${crewName}/config/config.yaml`;
      const response = await axios.get(configPath);
      const configData = yaml.load(response.data);

      // If theme configuration exists, apply it
      if (configData.frontend && configData.frontend.theme) {
        this.applyTheme(configData.frontend.theme, vuetify);
      }

      return configData;
    } catch (error) {
      console.error('Error loading theme configuration:', error);
      throw error;
    }
  },

  /**
   * Apply theme settings to Vuetify instance
   * @param {Object} theme - The theme configuration object
   * @param {Object} vuetify - The Vuetify instance
   */
  applyTheme(theme, vuetify) {
    if (!theme || !theme.colors) {
      console.warn('Theme configuration is missing or invalid');
      return;
    }

    try {
      // Apply dark mode if configured
      if (theme.hasOwnProperty('dark')) {
        vuetify.theme.dark = !!theme.dark;
      }

      // Apply color theme to both light and dark themes
      if (theme.colors) {
        Object.keys(theme.colors).forEach(colorName => {
          if (vuetify.theme.themes.light[colorName] !== undefined) {
            vuetify.theme.themes.light[colorName] = theme.colors[colorName];
            vuetify.theme.themes.dark[colorName] = theme.colors[colorName];
          }
        });
      }

      console.log('Theme applied successfully:', theme.colors);

      // Return the theme colors so components can access them
      return theme.colors;
    } catch (error) {
      console.error('Error applying theme:', error);
      throw error;
    }
  },

  /**
   * Get the current theme colors from Vuetify
   * @param {Object} vuetify - The Vuetify instance
   * @returns {Object} - Current theme colors
   */
  getCurrentThemeColors(vuetify) {
    return vuetify.theme.dark ? vuetify.theme.themes.dark : vuetify.theme.themes.light;
  }
}
