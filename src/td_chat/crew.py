from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from langchain_groq import ChatGroq
import os

# Importamos la función para cargar herramientas desde el servidor MCP
from src.td_chat.tools.mcp_client import load_tools_from_mcp

@CrewBase
class TdChat():
    """TdChat crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self):
        self.groq_llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="groq/gemma-7b-it"
        )

    @agent
    def report_assistant(self) -> Agent:
        # Cargamos las herramientas dinámicamente desde el servidor MCP
        mcp_tools = load_tools_from_mcp()
        return Agent(
            config=self.agents_config['report_assistant'], # type: ignore[index]
            tools=mcp_tools,
            verbose=True,
            allow_delegation=False,
            llm=self.groq_llm
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
            memory=True,
            cache=True
        )