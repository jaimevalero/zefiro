import yaml
import os
from loguru import logger
from jinja2 import Template

# Constants for file paths
YAML_RELATIVE_PATH = "etc/configs/hidalgos/config/"
JINJA_TEMPLATE_PATH = "meta_crew_backend/src/prompts/generate-files.j2"
STDOUT_PATH = "meta_crew_backend/src/prompts/generated"

# Load the YAML file as a dictionary
def load_file(filename):
    with open(os.path.join(YAML_RELATIVE_PATH, filename), 'r') as file:
        contents = yaml.load(file, Loader=yaml.FullLoader)
    return contents

# Load the agents and config YAML files
agents = load_file("agents.yaml")
config = load_file("config.yaml")

# Description for the new crew
description = """
1. Crew de Salud Mental Cotidiana
Problema: Ansiedad leve, estrés laboral o soledad (alta frecuencia, poco resuelto en etapas tempranas).

Roles:

Evaluador de Síntomas: Clasifica descripciones textuales del usuario (ej. "no puedo dormir") en categorías (estrés, ansiedad).

Generador de Recursos: Recomienda ejercicios de respiración o rutinas basadas en manuales de terapia en PDF.

Tracker de Progreso: Crea informes semanales con métricas simples (horas de sueño, energía autopercibida). 
"""

additional_instructions = """ Piensa cuidadosamente cuantos agentes harían falta, y genera una entrada por cada agente"""
# Load and render the Jinja2 template
with open(JINJA_TEMPLATE_PATH, "r") as file:
    template = Template(file.read())
    rendered = template.render(
        description=description, 
        example_yaml=yaml.dump(agents), 
        yaml_name="agents",
        additional_instructions=additional_instructions
    )

# Log the rendered template
logger.info(rendered)

# Save the rendered template to a file
generated_path = os.path.join(STDOUT_PATH, "agents.yaml")
os.makedirs(STDOUT_PATH, exist_ok=True)
with open(generated_path, "w") as file:
    file.write(rendered)

logger.info(f"Generated file at {generated_path}")