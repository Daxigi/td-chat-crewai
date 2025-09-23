from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_groq import ChatGroq
import os

# Asegúrate de que la ruta a tu cliente MCP sea correcta
from .tools.mcp_client import load_tools_from_mcp

@CrewBase
class TdChatCrew():
    """TdChat crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        # Define el LLM una sola vez para reutilizarlo
        self.groq_llm = ChatGroq(
            api_key=os.environ.get("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant"
        )
        # Carga las herramientas desde el servidor MCP
        self.mcp_tools = load_tools_from_mcp()

    @agent
    def request_router_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['request_router_agent'],
            llm=self.groq_llm
        )

    @agent
    def report_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config['report_assistant'],
            tools=self.mcp_tools,
            llm=self.groq_llm
        )

    @task
    def routing_task(self) -> Task:
        return Task(
            config=self.tasks_config['routing_task'],
            agent=self.request_router_agent()
        )

    @task
    def process_request_task(self) -> Task:
        return Task(
            config=self.tasks_config['process_request_task'],
            agent=self.report_assistant()
        )

    @crew
    def crew(self) -> Crew:
        """Crea y configura la Crew con un proceso secuencial."""
        return Crew(
            agents=[self.request_router_agent(), self.report_assistant()],
            tasks=[self.routing_task(), self.process_request_task()],
            process=Process.sequential,
            memory=True,
            # --- CORRECCIÓN AQUÍ ---
            # Cambiado de 'verbose=2' a 'verbose=True'
            verbose=True
        )