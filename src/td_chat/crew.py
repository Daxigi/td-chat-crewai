from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# Importamos la función para cargar herramientas desde el servidor MCP
from src.td_chat.tools.mcp_client import load_tools_from_mcp

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
            verbose=False,
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