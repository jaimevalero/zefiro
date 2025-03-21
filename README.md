# Meta-Crew : Quick automation of crews for crew.ai projects

## Description
With this project, you can easily create a crew for your crew.ai project. Only create a directory with the name of your crew and three files, and you are ready to go.

## Currents crews

| Crew Name      | Crew Description                          | Agents                                                                 | Tasks                                                                 | Config                                                                 | Caption                       | Report Example                                                                 |
|----------------|-------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|-------------------------------|------------------------------------------------------------------------------|
| rancho-relaxo  | App para bienestar mental y emocional     | [agentes IA](etc/configs/rancho-relaxo/config/agents.yaml)           | [Partes del informe](etc/configs/rancho-relaxo/config/tasks.yaml)             | [configuracion](etc/configs/rancho-relaxo/config/config.yaml)           | Mental wellness app          | [rancho-relax.md](meta-crew-frontend/static/examples/rancho-relax.md) ⭐      |
| footnotes      | App para corredores y atletas             | [agentes IA](etc/configs/footnotes/config/agents.yaml)               | [Partes del informe](etc/configs/footnotes/config/tasks.yaml)                 | [configuracion](etc/configs/footnotes/config/config.yaml)               | Running and athlete app      | [footnotes.md](meta-crew-frontend/static/examples/footnotes.md) ⭐            |
| dr-casa        | App para asistencia médica especializada  | [agentes IA](etc/configs/dr-casa/config/agents.yaml)                 | [Partes del informe](etc/configs/dr-casa/config/tasks.yaml)                   | [configuracion](etc/configs/dr-casa/config/config.yaml)                 | Specialized medical assistance app | [dr-casa.md](meta-crew-frontend/static/examples/dr-casa.md) ⭐                |
| hidalgos       | App para asistencia a personas de la tercera edad | [agentes IA](etc/configs/hidalgos/config/agents.yaml)           | [Partes del informe](etc/configs/hidalgos/config/tasks.yaml)                 | [configuracion](etc/configs/hidalgos/config/config.yaml)                | Elderly assistance app       | [hidalgos.md](meta-crew-frontend/static/examples/hidalgos.md) ⭐              |
| alphablocks    | Episode writer (development only)                           | [agentes IA](etc/configs/alphablocks/config/agents.yaml)             | [Partes del informe](etc/configs/alphablocks/config/tasks.yaml)               | [configuracion](etc/configs/alphablocks/config/config.yaml)             | Create scripts for episodes  | N/A                                                                          |

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
