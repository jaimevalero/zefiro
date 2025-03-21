# Meta-Crew : La IA que hace IAs


## Description
With this project, you can easily create crews for  crew.ai framework. 


## Currents crews

| Crew Name      | Crew Description                                                                                           | Caption                       | Report Example                                                                 |
|----------------|------------------------------------------------------------------------------------------------------------|-------------------------------|------------------------------------------------------------------------------|
| dr-casa        | App para asistencia médica especializada [agentes](etc/configs/dr-casa/config/agents.yaml) [tareas](etc/configs/dr-casa/config/tasks.yaml)     | Specialized medical assistance app | [dr-casa.md](meta-crew-frontend/static/examples/dr-casa.md) ⭐                |
| hidalgos       | App para asistencia a personas de la tercera edad [agentes](etc/configs/hidalgos/config/agents.yaml) [tareas](etc/configs/hidalgos/config/tasks.yaml) | Elderly assistance app       | [hidalgos.md](meta-crew-frontend/static/examples/hidalgos.md) ⭐              |
| rancho-relaxo  | App para bienestar mental y emocional [agentes](etc/configs/rancho-relaxo/config/agents.yaml) [tareas](etc/configs/rancho-relaxo/config/tasks.yaml) | Mental wellness app          | [rancho-relax.md](meta-crew-frontend/static/examples/rancho-relax.md) ⭐      |
| footnotes      | App para corredores y atletas [agentes](etc/configs/footnotes/config/agents.yaml) [tareas](etc/configs/footnotes/config/tasks.yaml)             | Running and athlete app      | [footnotes.md](meta-crew-frontend/static/examples/footnotes.md) ⭐            |
| alphablocks    | Episode writer (development only) [agentes](etc/configs/alphablocks/config/agents.yaml) [tareas](etc/configs/alphablocks/config/tasks.yaml)     | Create scripts for episodes  | N/A                                                                          |

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

5. Run Docker Compose to build and start the containers:
   ```bash
   docker compose down
   docker compose build
   docker compose up -d
   ```
6. Access with a browser at `http://localhost:3000` 

## Note:
This app need an open router token. This has a cost, from 0.10 $ to 0.15 $ per report
