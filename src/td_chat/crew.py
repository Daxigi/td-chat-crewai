from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# Importamos el OBJETO perezoso, no la función de carga
from src.td_chat.tools.mcp_client import tools

@CrewBase
class TdChat():
    """TdChat crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def report_assistant(self) -> Agent:
        # Ya no llamamos a la función de carga aquí.
        # Pasamos el objeto perezoso directamente al agente.
        return Agent(
            config=self.agents_config['report_assistant'], # type: ignore[index]
            tools=tools,
            verbose=True,
            allow_delegation=False
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
            memory=False,
            cache = False,
        )