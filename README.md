# Zéfiro : The AI that makes AIs

## Description

With this project, you can easily create your own crews for crew.ai framework, in a webapp.

## Current crews

(spanish translation below)

| Crew Name     | Description                              | Report Example                                                           |
| ------------- | ---------------------------------------- | ------------------------------------------------------------------------ |
| dr-casa       | Specialized medical assistance app       | [dr-casa-en.md](meta-crew-frontend/static/examples/dr-casa-en.md) ⭐     |
| hidalgos      | Elderly assistance app                   |                                                                          |
| rancho-relaxo | Mental wellness app                      |                                                                          |
| footnotes     | Running and athlete app                  |                                                                          |
| multilevel    | Educational adaptation for special needs |                                                                          |
| riskfolio     | Financial profiling app                  | [riskfolio-en.md](meta-crew-frontend/static/examples/riskfolio-en.md) ⭐ |

### Español

| Nombre de Crew            | Descripción                                                                                                                                                                                                                                                                                                                                                          | Ejemplo de Informe                                                                                 |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| dr-casa                   | App para asistencia médica especializada [agentes](etc/configs/dr-casa/config/agents.yaml) [tareas](etc/configs/dr-casa/config/tasks.yaml)                                                                                                                                                                                                                           | [dr-casa.md](meta-crew-frontend/static/examples/dr-casa.md) ⭐                                     |
| hidalgos                  | App para asistencia a personas de la tercera edad [agentes](etc/configs/hidalgos/config/agents.yaml) [tareas](etc/configs/hidalgos/config/tasks.yaml)                                                                                                                                                                                                                | [hidalgos.md](meta-crew-frontend/static/examples/hidalgos.md) ⭐                                   |
| rancho-relaxo             | App para bienestar mental y emocional [agentes](etc/configs/rancho-relaxo/config/agents.yaml) [tareas](etc/configs/rancho-relaxo/config/tasks.yaml)                                                                                                                                                                                                                  | [rancho-relax.md](meta-crew-frontend/static/examples/rancho-relax.md) ⭐                           |
| footnotes                 | App para corredores y atletas [agentes](etc/configs/footnotes/config/agents.yaml) [tareas](etc/configs/footnotes/config/tasks.yaml)                                                                                                                                                                                                                                  | [footnotes.md](meta-crew-frontend/static/examples/footnotes.md) ⭐                                 |
| multilevel                | App para adaptar examenes y lecciones a alumnos con necesidades específicas especiales (dislexia, espectro autista, deficit de atención, ...) [agentes](etc/configs/multilevel/config/agents.yaml) [tareas](etc/configs/multilevel/config/tasks.yaml)                                                                                                                | [multilevel.md](meta-crew-frontend/static/examples/multilevel.md) ⭐                               |
| riskfolio                 | App para análisis de perfiles financieros e inversión personalizada [agentes](etc/configs/riskfolio/config/agents.yaml) [tareas](etc/configs/riskfolio/config/tasks.yaml)                                                                                                                                                                                            | [riskfolio.md](meta-crew-frontend/static/examples/riskfolio.md) ⭐                                 |
| consumer-personas-creator | App para generar personas sintéticas altamente realistas para investigación de mercado con datos demográficos (INE/EPA), perfiles psicológicos (OCEAN, Schwartz), comportamiento de consumo y biografías narrativas coherentes [agentes](etc/configs/consumer-personas-creator/config/agents.yaml) [tareas](etc/configs/consumer-personas-creator/config/tasks.yaml) | [consumer-personas-creator.md](meta-crew-frontend/static/examples/consumer-personas-creator.md) ⭐ |

## Example Directory Structure

Example alphablocks crew:

```
alphablocks/
├── config
│   ├── agents.yaml #  Defines the roles, goals, backstories, and contexts for each Numberblock agent.
│   ├── tasks.yaml # Contains the descriptions and expected outputs for various tasks assigned to the Numberblock agents.
│   └── config.yaml # Configures the backend and frontend settings for the episode writer, including the nomination method and source of truth.
```

## Development

Create a python 3.11 virtual environment and install the requirements:

```bash
pip install -r meta_crew_backend/requirements.txt
```

## Docker build

To build and run the Docker containers, follow these steps:

1. Ensure Docker and Docker Compose are installed on your system.

2. Rename the ./meta_crew_backend/.env_template file to .env and change the token value to your own open router token.

3. Run Docker Compose to build and start the containers:
   ```bash
   docker compose down
   docker compose build
   docker compose up -d
   ```
4. Access with a browser at `http://localhost:3000`

## Note:

This app need an open router token. This has a cost, from 0.10 $ to 0.15 $ per report
