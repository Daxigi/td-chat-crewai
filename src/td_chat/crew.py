from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import time

task_start_time = None
# Importamos la función para cargar herramientas desde el servidor MCP
from src.td_chat.tools.mcp_client import load_tools_from_mcp

# funciones de callback para el inicio y fin de las tareas
def log_task_start(task_id, task_name):
    print(f"\n[{time.strftime('%H:%M:%S', time.localtime())}] INFO: Iniciando la tarea: {task_name}...")

def log_task_end(task_id, task_name, result):
    print(f"\n[{time.strftime('%H:%M:%S', time.localtime())}] INFO: Tarea finalizada: {task_name}. Duración: {time.time() - task_start_time:.2f} segundos.")


@CrewBase
class TdChat():
    """TdChat crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def report_assistant(self) -> Agent:
        # Cargamos las herramientas dinámicamente desde el servidor MCP
        mcp_tools = load_tools_from_mcp()
        return Agent(
            config=self.agents_config['report_assistant'], # type: ignore[index]
            tools=mcp_tools,
            verbose=True,
            allow_delegation=False  # <--- ¡Añade esta línea!
        )

    @task
    def process_request_task(self) -> Task:
        return Task(
            config=self.tasks_config['process_request_task'] # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the TdChat crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )