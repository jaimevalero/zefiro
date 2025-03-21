<template>
  <v-expansion-panels v-model="expanded">
    <v-expansion-panel>
      <v-expansion-panel-header>
        Términos de servicio y política de privacidad
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <v-card>
          <v-card-text>
            <div v-html="termsAndPolicyHtml"></div>
            <v-checkbox
              v-model="accepted"
              label="Acepto los términos de servicio y la política de privacidad"
              @change="onAcceptChange"
            ></v-checkbox>
          </v-card-text>
        </v-card>
      </v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script>
export default {
  name: 'TermsAndPolicy',
  data() {
    return {
      termsAndPolicyHtml: '',
      accepted: true, // Set to true by default
      expanded: [0] // Initially expanded
    }
  },
  watch: {
    // Add watcher to ensure panel closes when terms are accepted
    accepted(newValue) {
      if (newValue === true) {
        this.closePanel();
      }
    }
  },
  mounted() {
    this.loadTermsAndPolicy();
  },
  methods: {
    async loadTermsAndPolicy() {
      try {
        const response = await fetch('/terms_and_policy.html');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const text = await response.text();
        this.termsAndPolicyHtml = text;
      } catch (error) {
        console.error('Error loading terms and policy:', error);
        this.termsAndPolicyHtml = 'Error loading terms and conditions. Please try again later.';
      }
    },
    onAcceptChange() {
      this.$emit('accept-change', this.accepted);
    },
    closePanel() {
      this.expanded = [];
    }
  }
}
</script>

<style scoped>
</style>
