import re
import os
import json
import yaml

from loguru import logger

from typing import Dict, List, Optional, Union, Any, Callable
from pathlib import Path
from filelock import FileLock  # Import FileLock

from crewai import Agent, Crew, Task
from loguru import logger
import time  # Import time for sleep

from crewai import Crew
from pydantic import Field

from src.utils.models import get_model,get_model_name, get_provider,Provider
from src.utils.reports import convert_markdown_to_pdf

## Deried from the Crew class, the DerivedCrew class is used enrich the Crew class with additional attributes and methods.
class DerivedCrew(Crew):
    """
    Extension of the CrewAI Crew class with additional functionality for reporting and progress tracking.
    
    Following the Open-Closed Principle, this class extends Crew without modifying its core behavior,
    adding custom callbacks, reporting capabilities, and progress tracking.
    """
    # Define the fields explicitly for Pydantic
    tasks_done: int = Field(default=0)
    session_id: Optional[str] = Field(default=None)
    progress: float = Field(default=0.0)
    title: str = Field(default="")
    case: Optional[str] = Field(default=None)
    def __init__(self, agents, tasks, **kwargs):
        # Primero llamar a super().__init__() para inicializar correctamente Pydantic
        super().__init__(
            agents=agents,
            tasks=tasks,
            verbose=kwargs.get("verbose", True),
            process=kwargs.get("process", "sequential"),
            memory=kwargs.get("memory", False),
            name=kwargs.get("name", "Unnamed Crew"),
        )
        
        # Inicializar atributos adicionales
        self.tasks_done = 0
        self.session_id = kwargs.get("session_id", None)
        self.progress = 0
        self.title = ""        
        # Add additional attributes or methods here
    
    # Renamed the implementation to avoid naming conflict
    def step_callback(self, step_output):
        # If step_output is None, exit the function
        text = None
        try: 
            if step_output.result == 'None':
                return
        except:
            pass
    
        try:

            # If step_output is an AgentFinish object, , get the text from the agent output 
            if hasattr(step_output, 'text'):
                result_formatted = step_output.text
                result_formatted = result_formatted.replace("```markdown","").replace("```","").replace("*","")
                if result_formatted.lower().startswith("thought:"):
                    result_formatted = result_formatted.split("Thought:")[1].strip()
                elif result_formatted.lower().startswith("action:"):
                    result_formatted  = result_formatted.split("Action:")[1].strip()
                                    

                #result_formatted = next((line.split('Thought:')[1].strip() for line in step_output.text.split('\n') if 'Thought:' in line), "")

                if "\n" in result_formatted:
                    result_formatted = result_formatted.split("\n")[0]
                result_formatted+="\n"
                text = f"*Acción finalizada: {result_formatted}*" 
            elif hasattr(step_output, 'result'):
                # If there is no text attribute, exit the function
                if not hasattr(step_output.result, 'text'):
                    return
                result_formatted = step_output.text
                result_formatted = result_formatted.replace("```markdown","").replace("```","").replace("*","")
                # Coger solo hasta el primer salto de línea "\n"
                if "\n" in result_formatted:
                    result_formatted = result_formatted.split("\n")[0]
                result_formatted+="\n"
                text = f"*Respuesta bibliográfica: {result_formatted}*"
            if text:
                logger.info(f"Step output: {text}")
                # Coger solo hasta el primer salto de línea "\n"
                #self.task_callback(text, 0.0, "Procesando",self.session_id)
                percentage_progress = self.progress
                title = self.title
                progress_data = {
                    "log": text,
                    "progress": percentage_progress,
                    "title": title
                }
                self.write_progress_file(self.session_id, progress_data)


        except Exception as e:
            logger.error(f"Error in step callback: {e}")        

    def generate_consolidated_report(self,session_id):
        """
        Generate a consolidated report from all task outputs and save it to last_report.md.
        """
        logger.info("Generating consolidated report")

        # Initialize the report content
        report_content = ""

        # add sepearator en markdown
        # Iterate over the tasks and collect their outputs







        for i,task in enumerate(self.tasks):
            try :
                if task.name:
                    task_name = task.name
                elif task.expected_output:
                    task_name = task.expected_output
                else:
                    task_name = ""
                task_output = task.output.raw
                report_content += f"# {i} Informe: {task_name.replace('_', ' ').title()}\n\n{task_output}\n\n"
                report_content += "---\n\n"
            except Exception as e:
                logger.error(f"Error generating report: {e}")
        report_content = report_content.replace("```markdown","").replace("```","")
                
        # añade en markdown un informe de que el reporte se ha generado con IA
        # y que no constituye un diagnóstico médico, ni una prueba de cribado válida.
        report_content += "# Informe generado mediante inteligencia artificial.\n\n"
        report_content += "## Este informe no constituye un diagnóstico médico, ni una prueba de cribado válida. \n\n"
        report_content += "---\n\n"
        # Add the initial case at the start of the report
        report_content_initial = f"# Initial case: \n\n{self.case}\n\n"
        report_content_initial += "Fin del caso inicial\n\n---\n\n"  # Add end of initial case
        contenido_final = report_content_initial + report_content        
        
        if session_id:
            markdown_filename = f"logs/{session_id}_report.md"
        else :
            markdown_filename = "logs/last_report.md"

        if os.path.exists(markdown_filename):
            os.remove(markdown_filename)
        with open(markdown_filename, "w") as report_file:
            report_file.write(contenido_final)

    def convert_consolidated_report(self,session_id):

        # Generate un temp file with a unique name the content in pdf format. Return it
        if session_id:
            markdown_filename = f"logs/{session_id}_report.md"
            pdf_filename = f"logs/{session_id}.pdf" 
        else :
            markdown_filename = "logs/last_report.md"
            pdf_filename = f"logs/last_report.pdf"
        
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
                              
        try :
            convert_markdown_to_pdf(markdown_filename, pdf_filename)
            logger.info(f"Consolidated report generated and saved to {pdf_filename}")
  

            return pdf_filename
        except Exception as e:
            logger.error(f"Error generating pdf: {e}")
            return markdown_filename
                    
    def write_progress_file(self,session_id: str, progress_data: dict):
        """Write progress data to a JSON file with a file lock."""
        progress_file = f"tmp/{session_id}_progress.json"
        attempts = 3
        for attempt in range(attempts):
            try:
                logger.debug(f"Writing progress data to {progress_file}, intento {attempt + 1}")
                lock = FileLock(f"{progress_file}.lock")  # Create a lock for the progress file
                with lock:  # Use the lock when accessing the file
                    with open(progress_file, "w") as f:
                        f.write(json.dumps(progress_data))
                logger.debug(f"Progress data written to {progress_file} successfully")
                break  # Exit the loop if successful
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < attempts - 1:
                    time.sleep(3)  # Wait for 3 seconds before retrying
                else:
                    logger.error("All attempts to write the progress file have failed.")

    def callback_function(self,output):
        try :
            self.tasks_done += 1
            total_tasks = len(self.tasks)
            percentage_progress = self.tasks_done / total_tasks

            progress_message = f"""{output.raw}""".replace("```markdown","").replace("```","")
            title = f"({self.tasks_done}/{total_tasks}) Acabado el informe del {output.agent}"
            logger.info(progress_message)
            self.progress = percentage_progress
            self.title = title
            progress_data = {
                "log": progress_message,
                "progress": percentage_progress,
                "title": title
            }
            self.write_progress_file(self.session_id, progress_data)
        except Exception as e:
                logger.error(f"Error in callback function: {e}")

    def send_consolidated_report(self, pdf_filename, user_email, user_name="unknown"):
        """
        Send the consolidated report via email to the user.
        
        Following the Single Responsibility Principle, this method handles only
        the email sending logic, while generation and conversion are handled elsewhere.
        
        Args:
            pdf_filename: Path to the generated PDF file
            user_email: Email address of the recipient
            user_name: Name of the recipient (defaults to "unknown")
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Implement your email sending logic here
            logger.info(f"Sending consolidated report {pdf_filename} to {user_email} ({user_name})")
            # This is a placeholder - you'll need to implement actual email sending logic
            return True
        except Exception as e:
            logger.error(f"Error sending consolidated report: {e}")
            return False

    def create_crew_config(self):


        def load_yaml_with_backtick_handling(filename: str):
            """
            Read a file, remove triple-backticks if present, then parse as YAML.
            """
            try:
                with open(filename, "r") as f:
                    content = f.read()
                # Remove possible code fences
                content = content.replace("```yaml", "").replace("```", "").strip()
                return yaml.safe_load(content)
            except Exception as e:
                logger.error(f"Error loading YAML from {filename}: {e}")
                return None

        def transform_data(data):
            """
            Recursively traverse the YAML data and replace variables enclosed in curly braces 
            (e.g., {variable}) with '{case}'.
            
            The Pragmatic Programmer: Keep transformations DRY.
            Clean Code in Python: Use clear, self-explanatory functions.
            """
            if isinstance(data, dict):
                for k, v in data.items():
                    data[k] = transform_data(v)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    data[i] = transform_data(item)
            elif isinstance(data, str):
                # Replace patterns in strings using regex (Fluent Python: str methods are powerful)
                data = re.sub(r"\{(\w+)\}", "{case}", data)  # Reemplaza cualquier {variable} con {case}
                # If the string contains "(case)", replace it with "{case}"
                data = re.sub(r"\(case\)", "{case}", data)
                if "{case}" in data:
                    logger.debug(f"Transforming data: {data}")
            return data

        try:
            agents_data = load_yaml_with_backtick_handling("agents_created.yaml")
            config_data = load_yaml_with_backtick_handling("config_created.yaml")
            tasks_data = load_yaml_with_backtick_handling("tasks_created.yaml")

            # Zen of Python: "Explicit is better than implicit"
            agents_data = transform_data(agents_data)
            config_data = transform_data(config_data)
            tasks_data = transform_data(tasks_data)

            if not all([agents_data, config_data, tasks_data]):
                logger.error("Some YAML files did not load correctly.")
                return
        except Exception as e:
            logger.error(f"Overall error loading created YAML files: {e}")
            return

        codename = config_data.get("meta",{}).get("name", "default_codename")
        description = config_data.get("meta",{}).get("description", "default_description")
        target_dir = f"./etc/configs/{codename}"
        os.makedirs(target_dir, exist_ok=True)

        final_agents_path = os.path.join(target_dir, "agents.yaml")
        final_config_path = os.path.join(target_dir, "config.yaml")
        final_tasks_path = os.path.join(target_dir, "tasks.yaml")

        def save_yaml(data, path):
            """
            Save YAML data to a file, ensuring proper handling of special characters.
            
            - Fluent Python: Use libraries effectively.
            - Clean Code: Keep functions focused and clear.
            """
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True)  # Ensure special characters are saved correctly

        try:
            save_yaml(agents_data, final_agents_path)
            save_yaml(config_data, final_config_path)
            save_yaml(tasks_data, final_tasks_path)
            logger.info(f"Config crew created at: {target_dir}")
        except Exception as e:
            logger.error(f"Error saving YAML files to {target_dir}: {e}")

        # Load the global config yaml file in etc/configs/global-config.yaml
        global_config_path = "etc/configs/global-config.yaml"
        try:
            with open(global_config_path, "r", encoding="utf-8") as f:
                global_config = yaml.safe_load(f)
            logger.info(f"Global config loaded from {global_config_path}")

            # Verificar si el codename está en la lista global_config["app_list"]
            if codename not in global_config.get("app_list", {}):
                logger.info(f"Codename '{codename}' not found in global config. Adding it.")
                global_config["app_list"][codename] = description

                # Ordenar las claves de app_list alfabéticamente antes de guardar
                global_config["app_list"] = dict(sorted(global_config["app_list"].items()))

                # Guardar el archivo YAML actualizado
                with open(global_config_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(global_config, f, allow_unicode=True)  # Ensure special characters are saved correctly
                logger.info(f"Codename '{codename}' added to global config and saved to {global_config_path}")
            else:
                logger.info(f"Codename '{codename}' already exists in global config. No changes made.")
        except Exception as e:
            logger.error(f"Error handling global config at {global_config_path}: {e}")

    def kickoff(self, inputs: Dict[str, Any]):
        """
        Start the execution of the crew's tasks.
        
        This method overrides the kickoff method of the Crew class to inject custom callbacks
        into agents and tasks before starting the execution.
        
        Args:
            inputs: Dictionary of inputs to pass to the tasks
        """
        # Inyectar los callbacks a agents y tasks
        case = inputs.get("case",None)
        if case:
            self.case = case
        for agent in self.agents:
            agent.step_callback = self.step_callback
            
        for task in self.tasks:
            task.callback = self.callback_function
        command_types = [ 'long', 'short', 'entity', 'knowledge',                'kickoff_outputs']
        for command_type in command_types:
            try :
                self.reset_memories(command_type = command_type)
            except Exception as e:
                logger.error(f"Error resetting memories: {e}")

      
        # Llamar al método kickoff de la superclase
        results = super().kickoff(inputs)

        if self.name == "zefiro" :
            # Execute the function create_crew_config
            self.create_crew_config()

        return results
