#!/usr/bin/env python
"""
CrewFactory - A factory class for creating crews with different configurations.

This module implements the Factory Method design pattern to encapsulate crew creation
and configuration logic, promoting separation of concerns and making the system more maintainable.
"""
import re
import os
import json
import yaml
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from filelock import FileLock  # Import FileLock

from crewai import Agent, Crew, Task
from loguru import logger
import time  # Import time for sleep

from src.derived_crew import DerivedCrew
from src.utils.models import get_model,get_model_name, get_provider,Provider


def run_wrapper(crew_name:str, case:str, websocket_callback, session_id:str, user_email="unknown", user_name="unknown"):
    if not case:
        # case = get_case()
        raise Exception("Case is required")
    inputs = {
        'case': case
    }
    factory = CrewFactory(crew_name,session_id=session_id)
    crew =factory.build_crew_from_config(case)
    inputs = {
            'case': case
        }
    crew.kickoff(inputs)
    crew.generate_consolidated_report(session_id)
    # Conver to pdf
    pdf_filename = crew.convert_consolidated_report(session_id)
    # Send email
    crew.send_consolidated_report(pdf_filename, user_email, user_name)

    # Print token usage
    logger.info(f"Token usage: {crew.usage_metrics}")
        
    return pdf_filename


    
def ensure_dirs_exist():
    dirs = ["logs", "tmp"]
    # Ensure the directories exist in the current working directory
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)
            logger.info(f"Created directory {dir}")



class CrewFactory:
    """
    A factory class for creating and configuring CrewAI crews.
    
    This class follows the Factory Method pattern to abstract the crew creation process,
    allowing for various crew configurations without modifying client code.
    
    Attributes:
        config_dir (Path): Directory containing crew configuration files.
        llm_config (Dict): Configuration for the language model.
    """
    
    def __init__(self, crew_name, session_id: str = None):
        """
        Initialize the CrewFactory with configuration settings.
        
        Args:
            config_dir: Directory containing crew configuration files (agents.yaml, tasks.yaml, etc.)
            llm_config: Configuration for the language model to be used by the crew
        """
        config_dir = f"etc/configs/{crew_name}/config"
        current_dir = os.getcwd()
        if not os.path.exists(config_dir):
            raise FileNotFoundError(f"Configuration directory '{config_dir}' not found")

        self.crew_name = crew_name
        self.config_dir = Path(config_dir) 
        logger.info(f"Initialized CrewFactory with {current_dir=} , {self.config_dir=}")

        if session_id:
            self.session_id = session_id
        self.tasks_done = 0


    def load_config(self, filename: str) -> Dict:
        """
        Load configuration from a YAML file, trying in current directory, parent, and grandparent.
        Using absolute paths for better logging and debugging.
        """
        # Start with the current config directory and convert to absolute path
        current_path = os.path.abspath(self.config_dir)
        
        max_levels = 3
        level = 0
        tried_paths = []
        
        while level < max_levels:
            # Build and store the absolute path
            full_path = os.path.abspath(os.path.join(current_path, filename))
            tried_paths.append(full_path)
            
            # Log the absolute path for clarity
            logger.debug(f"Attempting to load config from (absolute path): {full_path}")
            
            if os.path.exists(full_path):
                logger.info(f"Found configuration at level {level} (absolute path): {full_path}")
                try:
                    with open(full_path, 'r') as file:
                        return yaml.safe_load(file)
                except yaml.YAMLError as e:
                    logger.error(f"Error parsing YAML from (absolute path): {full_path}: {e}")
                    raise
            
            # Move up to parent directory (using absolute path)
            parent_path = os.path.dirname(current_path)
            
            # Check if we've reached the root directory
            if parent_path == current_path:
                break
                
            current_path = parent_path
            level += 1
            #logger.debug(f"Moving up to parent directory (absolute path): {current_path}")
        
        # Error message with absolute paths
        error_msg = f"Configuration file '{filename}' not found in any of these absolute paths: {', '.join(tried_paths)}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    def _select_agent_names(self, agent_configs: Dict, crew_config: Dict, case: str) -> List[str]:
        """
        Select which agents to use based on the nomination method (all or prompt).
        
        Args:
            agent_configs: Dictionary of available agent configurations
            crew_config: Crew configuration containing nomination method
            case: The specific case to be handled
            
        Returns:
            List of agent names in execution order
            
        Raises:
            ValueError: If the nomination method is invalid or LLM selection fails
        """
        method = crew_config["backend"]["nomination"]["method"]
        possible_agent_names = list(agent_configs.keys())
        possible_agent_names_lower = [name.lower() for name in possible_agent_names]
        
        # Simple case: select all agents
        if method["type"].lower() == "all":
            return possible_agent_names
            
        # LLM-based selection
        if method["type"].lower() != "prompt":
            raise ValueError(f"Election method type '{method['type']}' not implemented")
            
        formatted_prompt = re.sub(r'\{\s*case\s*\}', case, method['prompt'])
        
        # Try multiple times to get valid agent selection from LLM
        MAX_ITERATIONS = 3
        current_iteration = 0
        extra_prompt = ""
        llm = get_model("MAIN")

        short_agent_configs = {}
        for agent_name, agent_config in agent_configs.items():
            short_agent_configs[agent_name] = {}
            if "role" in agent_config:
                short_agent_configs[agent_name]["role"]= agent_config.get("role", "")
            if "backstory" in agent_config: 
                short_agent_configs[agent_name]["backstory"]= agent_config.get("backstory", "")

            
        while current_iteration < MAX_ITERATIONS:
            try:
                
                final_prompt = f"""
{formatted_prompt}. 

{short_agent_configs} <case>{case}</case> 
{extra_prompt}
Important: You MUST respond ONLY with a JSON array of agent names, from values {possible_agent_names}.
"""
                logger.info(f"Prompting LLM to select agents {final_prompt}")
                
                # if llm has attr call, use it, else use complete                

                if hasattr(llm, "call"):
                    response = llm.call(final_prompt)
                    short_response = response
                    logger.info(f"LLM response: {response}")
                else: 
                    response = llm.complete(final_prompt)
                    short_response = response.text[response.text.find("["):response.text.rfind("]")+1]
                    logger.info(f"LLM response: {response.text}")
                # Get only from '[' character to the  ']' character
                
                agent_names = json.loads(short_response)
                logger.info(f"LLM response: {agent_names}")
                
                # Convert agent names to lower case for comparison
                agent_names_lower = [name.lower() for name in agent_names]
                
                # Apply fixed position agents (first and last)
                self._apply_fixed_position_agents(agent_names_lower, crew_config, possible_agent_names_lower)
                
                # Verify all selected agents exist in configuration
                if all(name in possible_agent_names_lower for name in agent_names_lower):
                    # Adjust agent_names to match the original case in possible_agent_names
                    agent_names = [possible_agent_names[possible_agent_names_lower.index(name)] for name in agent_names_lower]
                    return agent_names
                    
                extra_prompt = f" Invalid agent selection. Please only choose from: {possible_agent_names}. Error: {response.text}"
                current_iteration += 1
                
            except Exception as e:
                current_iteration += 1
                extra_prompt = f" Error: {str(e)}. Previous response: {response.text}"
                logger.error(f"LLM agent selection failed: {e}")
                
        raise ValueError(f"Failed to get valid agent selection after {MAX_ITERATIONS} attempts")

    def _apply_fixed_position_agents(self, agent_names: List[str], crew_config: Dict, possible_agent_names: List[str]) -> None:
        """
        Apply any fixed-position agents (first/last) according to configuration.
        Modifies the agent_names list in place.
        
        Args:
            agent_names: List of agent names to modify
            crew_config: Configuration containing fixed position settings
            possible_agent_names: All available agent names for validation
            
        Raises:
            ValueError: If a fixed position agent is not available
        """
        first_agent = crew_config["backend"]["nomination"].get("always_first_agent")
        last_agent = crew_config["backend"]["nomination"].get("always_last_agent")
        
        # Process first agent if specified
        if first_agent:
            first_agent_lower = first_agent.lower()
            if first_agent_lower not in possible_agent_names:
                raise ValueError(f"First agent '{first_agent}' not in available agents list")
                
            # Remove if already in list to avoid duplicates
            if first_agent_lower in agent_names:
                agent_names.remove(first_agent_lower)
            
            # Insert at beginning    
            agent_names.insert(0, first_agent_lower)
            
        # Process last agent if specified
        if last_agent:
            last_agent_lower = last_agent.lower()
            if last_agent_lower not in possible_agent_names:
                raise ValueError(f"Last agent '{last_agent}' not in available agents list")
                
            # Remove if already in list to avoid duplicates
            if last_agent_lower in agent_names:
                agent_names.remove(last_agent_lower)
                
            # Append at end
            agent_names.append(last_agent_lower)

    def _create_agents_from_names(self, agent_names: List[str], agent_configs: Dict, ) -> List[Agent]:
        """
        Create Agent instances from the selected agent names.
        
        Args:
            agent_names: Names of agents to create
            agent_configs: Configuration data for all agents
            callback_function: Optional callback function to inject into agents
            
        Returns:
            List of instantiated Agent objects
        """
        model = get_model("MAIN")  # Get model once for efficiency
        agents = []
        
        for agent_name in agent_names:
            if agent_name not in agent_configs:
                logger.warning(f"Agent '{agent_name}' not found in configuration, skipping")
                continue
                
            agent_config = agent_configs[agent_name]

            
            agents.append(Agent(**agent_config, llm=model))
            
        return agents

    def _create_tasks_with_context(self, agent_names: List[str], task_configs: Dict, agent_configs: Dict, callback_function: Optional[Any] = None) -> List[Task]:
        """
        Create tasks for the selected agents and resolve their context relationships.
        This unified function handles both task creation and context management.
        
        Args:
            agent_names: Names of selected agents
            task_configs: Configuration data for all tasks
            agent_configs: Configuration data for all agents
            callback_function: Optional callback function to inject into tasks
            
        Returns:
            List of fully configured Task objects with contexts resolved
        """
        # Deep copy to avoid modifying the original during processing
        task_configs_copy = json.loads(json.dumps(task_configs))
        model = get_model("MAIN")
        
        # First pass: create all tasks and store context references
        task_dict = {}  # Maps task name to Task object
        context_dict = {}  # Maps task name to list of context task names
        
        for task_name, config in task_configs.items():
            agent_name = config.get("agent")
            
            # Only create tasks for selected agents
            if agent_name not in agent_names:
                continue
                
            # Create mutable copy of configuration
            task_config = config.copy()
            if callback_function:
                task_config["callback"] = callback_function
            
            # Extract special properties
            agent_name = task_config.pop("agent")
            context_refs = task_config.pop("context", [])
            
            # Filter context to only include tasks for selected agents
            valid_context = [
                ref for ref in context_refs 
                if ref in task_configs_copy and task_configs_copy[ref].get("agent") in agent_names
            ]
            
            # Create the task
            task = Task(
                agent=Agent(**agent_configs[agent_name], llm=model),
                **task_config
            )
            
            # Store for second pass
            task_dict[task_name] = task
            context_dict[task_name] = valid_context
        
        # Second pass: link tasks to their context tasks
        for task_name, context_names in context_dict.items():
            if not context_names:
                continue
                
            # Find and link context tasks
            try:
                context_tasks = [task_dict[name] for name in context_names if name in task_dict]
                if context_tasks:
                    task_dict[task_name].context = context_tasks
            except Exception as e:
                logger.warning(f"Error linking context for task '{task_name}': {e}")
        
        return list(task_dict.values())
    
    def select_agents_tasks(self, agent_configs: Dict, task_configs: Dict, crew_config: Dict, case: str) -> tuple:
        """
        Orchestrates the selection of agents and creation of tasks based on the configuration.
        
        This method delegates to specialized factory methods for:
        1. Selecting which agents to use
        2. Creating agent instances
        3. Creating and configuring tasks with their contexts
        
        Args:
            agent_configs: Dictionary of agent configurations
            task_configs: Dictionary of task configurations
            crew_config: Crew configuration
            case: The specific case to handle
            callback_function: Optional callback function to inject into agents and tasks
            
        Returns:
            Tuple of (agents, tasks) ready for crew creation
        """
        try:
            # Step 1: Select which agent names to use
            agent_names = self._select_agent_names(agent_configs, crew_config, case)
            logger.info(f"Selected agent names: {agent_names}")
            
            # Step 2: Create agent instances
            agents = self._create_agents_from_names(agent_names, agent_configs)
            logger.info(f"Created {len(agents)} agents")
            
            # Step 3: Create tasks with context
            tasks = self._create_tasks_with_context(agent_names, task_configs, agent_configs)
            logger.info(f"Created {len(tasks)} tasks with context")
            
            return agents, tasks
            
        except Exception as e:
            logger.exception(f"Error in agent/task selection: {e}")
            raise

    def create_crew(self, name: str, agents: List[Agent], tasks: List[Task], **kwargs) -> Crew:
        """
        Create a crew instance with the specified agents and tasks.
        
        This method implements the Factory Method pattern by instantiating a DerivedCrew
        with the appropriate configuration and passing all necessary parameters.
        
        Args:
            name: Name of the crew
            agents: List of agents to include in the crew
            tasks: List of tasks for the crew to perform
            **kwargs: Additional arguments to pass to the DerivedCrew constructor
            
        Returns:
            Configured DerivedCrew instance
        """
        logger.info(f"Creating crew: {name} with {len(agents)} agents and {len(tasks)} tasks")
        
        # Pass session_id and embedder explicitly, along with other parameters
        return DerivedCrew(
            agents=agents,
            tasks=tasks,
            verbose=kwargs.get("verbose", True),
            process=kwargs.get("process", "sequential"),
            memory=kwargs.get("memory", False),
            name=name,
            session_id=self.session_id,
            embedder=kwargs.get("embedder"),
        )
    
    def build_crew_from_config(self , case:str) -> Crew:
        """
        Build a complete crew from configuration files.
        
        This is the main factory method that creates a fully configured crew
        based on configuration files in the specified directory.
        
        Args:
            case: The specific case to handle
            
        Returns:
            Fully configured Crew instance
            
        Raises:
            FileNotFoundError: If required configuration files are missing
        """
        crew_name = self.crew_name
        try:
            # Load configurations from the crew-specific directory
            agent_configs = self.load_config("agents.yaml")
            task_configs = self.load_config("tasks.yaml")
            crew_config = self.load_config("config.yaml")
            
            # Create agents and tasks
            agents, tasks = self.select_agents_tasks(agent_configs, task_configs, crew_config, case, )
            
            embed_model_name = get_model_name("EMBED")
            provider = "ollama" if get_provider("MAIN") == Provider.OLLAMA else "openai"

            # Create and return the crew
            return self.create_crew(
                name=crew_config.get("name", crew_name),
                embedder={
                    "provider": provider,
                    "config": {
                        "model": embed_model_name
                    }
                },
                agents=agents,
                tasks=tasks,
                verbose=crew_config.get("verbose", True),
                process=crew_config.get("process", "sequential"),
                memory=crew_config.get("memory", False),
            )
            
        except FileNotFoundError as e:
            logger.error(f"Failed to build crew '{crew_name}': {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while building crew '{crew_name}': {e}")
            raise

# Example of usage
if __name__ == "__main__":
    # Create a CrewFactory instance
    # crew_name = "alphablocks"
    # case = """Hazme un capitulo de alphablocks donde solo hablen los personajes de alphablock de números impares"""
    crew_name = "dr-casa"
    case = """ Ayuda a preparar un caso para la presentación a un médico humano. 
1) Sugiere posibles dolencias que casen con los sintomas descritos . 
2) preguntas que un doctor humano haría al paciente para conducir al diagnóstico 
3) ejemplos de comportamientos que podrían ayudar al paciente (dietas, ejercicios) 
4) resumen de todo, para poder explicar a un doctor humano tanto los sintomas como las principales opciones de posibles diágnosticos. No uses JSON ni mermaid.

Directrices:
El objetivo principal es identificar la causa raíz de los síntomas y proporcionar un plan claro y accionable para su resolución. Combinamos un análisis exhaustivo de los registros médicos, un razonamiento basado en evidencia y un formato de respuesta estructurado para brindar la mejor atención posible.

Mentalidad y Enfoque
Identificación de la Causa Raíz: El enfoque principal es descubrir la causa fundamental de los problemas de salud mediante un análisis integral y un razonamiento lógico.

Decisiones Basadas en Datos: Cada conclusión se fundamenta en evidencia médica y se adapta a los datos y el contexto del paciente.

Enfoque Sistemático y Holístico: Se integran datos de diferentes especialidades y se evalúan los síntomas en conjunto, evitando interpretaciones aisladas.

Principios de Respuesta
Al responder a los pacientes, el enfoque se estructura de la siguiente manera:

Causa Raíz
Escenarios: Explicar las posibles causas basadas en los datos del paciente, incluyendo su probabilidad y la evidencia que las respalda.
Evidencia de Apoyo: Proporcionar un razonamiento claro para cada escenario.
Evidencia Contradictoria: Destacar cualquier dato que pueda refutar o debilitar un escenario específico, asegurando un análisis equilibrado.
Plan de Acción
Pruebas y Acciones: Proponer pruebas diagnósticas o pasos específicos para confirmar o descartar las causas sospechadas.
Justificación: Explicar el propósito de cada prueba o acción y lo que se espera descubrir.
Próximos Pasos: Describir cómo proceder según los posibles resultados de las pruebas o acciones. Por ejemplo:
Si el resultado es A: "Esto confirma la causa X, y aplicaremos el Plan Y."
Si el resultado es B: "Esto sugiere una causa alternativa, por lo que seguiremos el Plan Z."
Principios de Ejecución
Proceso Iterativo: El diagnóstico y el tratamiento evolucionan con nueva información. Cada paso refina la comprensión de la condición del paciente.
Transparencia: Las explicaciones son claras, brindando a los pacientes una comprensión completa de la lógica detrás de las recomendaciones.
Empatía y Precisión: Se prioriza tanto el alivio inmediato como los resultados a largo plazo, asegurando que cada acción contribuya a una recuperación duradera.




"""
    crew_name = "footnotes"
    case = """Caso clínico: Runner semiprofesional - Preparación para Maratón de Madrid
Datos del paciente

Nombre: Carlos Martínez
Edad: 32 años
Sexo: Masculino
Ocupación: Ingeniero informático y runner semiprofesional
Objetivo: Prepararse para el Maratón de Madrid (a realizarse en 8 semanas)

Historia deportiva

Runner semiprofesional con 8 años de experiencia en competiciones
Mejor marca personal en maratón: 2h 42min (hace 2 años)
Entrena habitualmente 70-80 km semanales
Ha participado en 7 maratones y numerosas carreras de distancias menores
Objetivo para Madrid: terminar por debajo de 2h 40min

Historia médica relevante

Lesiones previas:

Tendinitis de Aquiles bilateral (hace 3 años, recurrente en pie derecho)
Fascitis plantar (hace 18 meses)
Síndrome de la cintilla iliotibial (hace 10 meses)
Esguince de tobillo grado II (hace 5 meses)


Condiciones actuales:

Dolor persistente en cara externa de rodilla derecha durante carreras >10km
Molestias en tendón de Aquiles derecho tras entrenamientos intensos
Sensación de entumecimiento en dedos del pie izquierdo después de correr >15km
Dolor lumbar ocasional tras series largas de velocidad



Situación actual

Se encuentra a 8 semanas del Maratón de Madrid
Entrenamiento actual: 55-60 km semanales (reducido por molestias)
Últimas 3 semanas con dificultad para completar entrenamientos largos
Ha reducido las series de velocidad por dolor lumbar
Experimenta fatiga inusual y recuperación más lenta tras entrenamientos intensos

Historial nutricional

Dieta variada pero sin planificación específica para rendimiento
Hidratación: aproximadamente 2L diarios
Suplementación actual: proteína de suero después de entrenamientos
No ha realizado periodización nutricional para competiciones previas

Otros datos relevantes

Calzado: renovado hace 2 meses (350km de uso)
Terrenos de entrenamiento: 70% asfalto, 20% tierra, 10% pista
Análisis biomecánico realizado hace 1 año identificó ligera pronación
Usa plantillas personalizadas desde hace 6 meses
Trabajo sedentario (8-10 horas sentado frente a ordenador)
Duerme 6-7 horas diarias
Niveles de estrés moderados-altos por presión laboral

Preocupaciones del paciente

Llegar en condiciones óptimas a la competición
Prevenir recaída de lesiones durante la preparación
Optimizar la recuperación entre entrenamientos
Adoptar estrategias nutricionales para mejorar rendimiento
Conseguir su objetivo de tiempo (<2h 40min)
Mantener el equilibrio entre entrenamiento y vida profesional"""
    crew =CrewFactory(crew_name,session_id="0000").build_crew_from_config(case)
    inputs = {
            'case': case
        }
    crew.kickoff(inputs)
    a = 0
    for task in crew.tasks:
        a +=1
        logger.info(f"Task {a}: {task.name}")
        logger.info(task.output.raw)
        logger.info("\n\n")

    logger.info(f"Finished crew execution"  )
    logger.info(f"Memory: {crew.memory}")
