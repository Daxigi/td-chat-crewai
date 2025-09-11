from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class TdChat():
    """TdChat crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def analista_de_peticiones(self) -> Agent:
        return Agent(
            config=self.agents_config['analista_de_peticiones'], # type: ignore[index]
            verbose=True
            # Aquí es donde añadirías las tools más adelante
            # tools=[mi_herramienta_1, mi_herramienta_2]
        )

    @agent
    def formulador_de_respuestas(self) -> Agent:
        return Agent(
            config=self.agents_config['formulador_de_respuestas'], # type: ignore[index]
            verbose=True
        )

    @task
    def analizar_peticion_task(self) -> Task:
        return Task(
            config=self.tasks_config['analizar_peticion_task'], # type: ignore[index]
        )

    @task
    def formular_respuesta_task(self) -> Task:
        return Task(
            config=self.tasks_config['formular_respuesta_task'], # type: ignore[index]
            # Eliminamos output_file para obtener la respuesta como texto
        )

    @crew
    def crew(self) -> Crew:
        """Creates the TdChat crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )