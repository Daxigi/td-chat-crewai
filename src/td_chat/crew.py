from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# Importamos el OBJETO perezoso, no la función de carga
from src.td_chat.tools.mcp_client import tools
# Importamos la herramienta de RAG
from src.td_chat.tools.rag_tool import tramites_rag_tool

@CrewBase
class TdChat():
    """TdChat crew"""

    agents: List[BaseAgent]
    tasks: List[Task]
    
    # Callback opcional para reporte de progreso
    step_callback: object = None

    @agent
    def report_assistant(self) -> Agent:
        # Ya no llamamos a la función de carga aquí.
        # Pasamos el objeto perezoso directamente al agente.
        return Agent(
            config=self.agents_config['report_assistant'], # type: ignore[index]
            tools=list(tools),
            verbose=True,
            max_iter=20,
            allow_delegation=False,
            step_callback=self.step_callback
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

@CrewBase
class PublicCrew():
    """Crew para el bot público de información"""
    agents_config = 'config/public_agents.yaml'
    tasks_config = 'config/public_tasks.yaml'
    
    agents: List[BaseAgent]
    tasks: List[Task]
    step_callback: object = None

    @agent
    def municipal_informant(self) -> Agent:
        return Agent(
            config=self.agents_config['municipal_informant'],
            tools=[tramites_rag_tool],
            verbose=True,
            allow_delegation=False,
            step_callback=self.step_callback
        )

    @task
    def inform_task(self) -> Task:
        return Task(
            config=self.tasks_config['inform_task']
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
            memory=False
        )