import Vue from 'vue';
import { loadGapiInsideDOM } from 'gapi-script';

// Load environment variables
const clientId = process.env.VUE_APP_GOOGLE_CLIENT_ID;

// Configuration object for Google OAuth 2.0
const gauthOption = {
  clientId: clientId,
  scope: 'profile email',
  prompt: 'select_account'
};

// Function to dynamically load the Google API script with proper CSP handling
function loadGoogleApiScript() {
  const script = document.createElement('script');
  script.src = 'https://apis.google.com/js/platform.js';
  script.async = true;
  script.defer = true;
  document.head.appendChild(script);
  script.onload = () => {
    window.gapi.load('auth2', () => {
      window.gapi.auth2.init(gauthOption).then(() => {
        // Ensure the auth instance is available
        Vue.prototype.$googleAuth = window.gapi.auth2.getAuthInstance();
      }).catch(error => {
        console.error('Error initializing Google Auth:', error);
      });
    });
  };
}
console.log('Loading Google API script...');

// Load the Google API script
loadGoogleApiScript();

// Create a Vue plugin to handle Google authentication
const GoogleAuthPlugin = {
  install(Vue) {
    Vue.prototype.$googleAuth = null;
  }
};

// Use the GoogleAuthPlugin with Vue
Vue.use(GoogleAuthPlugin);
