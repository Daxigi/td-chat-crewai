from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_groq import ChatGroq
import os

# --- IMPORTACIÓN CORRECTA ---
# Importamos la función que carga las herramientas desde tu servidor MCP
# Asegúrate de que tu archivo mcp_client.py esté en la ruta: src/td_chat/tools/mcp_client.py
from .tools.mcp_client import load_tools_from_mcp

@CrewBase
class TdChatCrew():
    """TdChat crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        # Define el LLM una sola vez para reutilizarlo en los agentes
        self.groq_llm = ChatGroq(
            api_key=os.environ.get("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant"
        )
        # --- CARGA DINÁMICA DE HERRAMIENTAS ---
        # Llama a tu función para obtener las herramientas desde el servidor
        self.mcp_tools = load_tools_from_mcp()

    @agent
    def request_router_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['request_router_agent'],
            llm=self.groq_llm
            # Este agente no necesita herramientas
        )

    @agent
    def report_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config['report_assistant'],
            tools=self.mcp_tools, # Asigna las herramientas cargadas desde el MCP
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
            verbose=2
        )