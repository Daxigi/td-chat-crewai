from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from src.td_chat.tools.report_tools import (
    EstadoUltimaSolicitudUsuarioTool,
    ConteoEstadosTramiteEspecificoTool,
    SolicitudesPorEstadoTool,
    ListAvailableReportsTool,
    ObtenerRolesUsuarioTool,
    ListarAgentesTool,
    ConsultarAtencionesAgenteTool,
    ConsultarAtencionesAgentePorTramiteTool
)

@CrewBase
class TdChat():
    """TdChat crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def report_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config['report_assistant'], # type: ignore[index]
            tools=[
                EstadoUltimaSolicitudUsuarioTool(),
                ConteoEstadosTramiteEspecificoTool(),
                SolicitudesPorEstadoTool(),
                ListAvailableReportsTool(),
                ObtenerRolesUsuarioTool(),
                ListarAgentesTool(),
                ConsultarAtencionesAgenteTool(),
                ConsultarAtencionesAgentePorTramiteTool()
            ],
            verbose=True
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
            verbose=True,
        )