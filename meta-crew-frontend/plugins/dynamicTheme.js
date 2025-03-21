import axios from 'axios'
import yaml from 'js-yaml'

export default async function ({ app }) {
  // Only run on client-side
  if (typeof window !== 'undefined') {
    try {
      const urlParams = new URLSearchParams(window.location.search)
      const crewName = urlParams.get('crew_name')

      console.log(`Theme plugin initialized, crew name: ${crewName || 'not specified'}`)

      if (crewName) {
        // Usamos una URL absoluta para cargar el archivo de configuración
        const configPath = `/etc/configs/${crewName}/config/config.yaml`
        console.log(`Attempting to load config from: ${configPath}`)

        try {
          const response = await axios.get(configPath)
          console.log('Config response received:', response)

          const configData = yaml.load(response.data)
          console.log('Config loaded successfully:', configData)

          // Verificamos que la configuración de tema exista
          if (configData.frontend && configData.frontend.theme) {
            console.log('Theme configuration found:', configData.frontend.theme)

            // // Aplicamos el modo oscuro/claro
            // if (configData.frontend.theme.dark !== undefined) {
            //   console.log(`Setting dark mode to: ${configData.frontend.theme.dark}`)
            //   app.$vuetify.theme.dark = configData.frontend.theme.dark
            // }

            // Aplicamos los colores del tema
            if (configData.frontend.theme.colors) {
              console.log('Applying theme colors:', configData.frontend.theme.colors)

              // Aplicamos los colores a ambos temas (claro y oscuro)
              Object.keys(configData.frontend.theme.colors).forEach(colorName => {
                const colorValue = configData.frontend.theme.colors[colorName]

                // if (app.$vuetify.theme.themes.light &&
                //     colorName in app.$vuetify.theme.themes.light) {
                //   console.log(`Setting ${colorName} to ${colorValue} in light theme`)
                //   app.$vuetify.theme.themes.light[colorName] = colorValue
                // }

                // if (app.$vuetify.theme.themes.dark &&
                //     colorName in app.$vuetify.theme.themes.dark) {
                //   console.log(`Setting ${colorName} to ${colorValue} in dark theme`)
                app.$vuetify.theme.themes.dark[colorName] = colorValue
                // }
              })

              // Forzamos la actualización del tema
              // console.log('Forcing theme update...')
              // const originalDark = app.$vuetify.theme.dark
              // app.$vuetify.theme.dark = !originalDark  // Cambiamos temporalmente
              // setTimeout(() => {
              //   app.$vuetify.theme.dark = originalDark  // Restauramos
              //   console.log('Theme updated with new colors')
              // }, 50)
            }

            console.log(`Applied dynamic theme for crew: ${crewName}`)
          } else {
            console.warn('No theme configuration found in the YAML file')
          }
        } catch (configError) {
          console.error('Error loading or parsing config:', configError)
          if (configError.response) {
            console.error('Config response error:', configError.response.status, configError.response.statusText)
          }
        }
      } else {
        console.warn('No crew_name specified in URL, skipping theme customization')
      }
    } catch (error) {
      console.error('General error in dynamicTheme plugin:', error)
    }
  } else {
    console.log('dynamicTheme plugin running on server side, skipping')
  }
}
