FROM node:20-alpine

WORKDIR /app

COPY meta-crew-frontend/package*.json ./
RUN npm install

COPY meta-crew-frontend /app

# Ensure the nuxt command is correctly configured
RUN npm install -g nuxt

# Copy logs to a more accessible location
RUN mkdir -p /app/logs

# replace http://127.0.0.1:8000 for http://backend:8000 in /app/.nuxt/utils.js
RUN [ -f /app/.nuxt/utils.js ] && sed -i 's|http://127.0.0.1:8000|http://epg-wellness:8000|g' /app/.nuxt/utils.js || echo "/app/.nuxt/utils.js not found, skipping replacement"

# Start process on port 3000
CMD ["sh", "-c", "npm run dev -- --port 3000"]