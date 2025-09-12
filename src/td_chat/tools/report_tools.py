from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import sqlite3 # Placeholder import

# Placeholder for database connection
# You will need to replace this with your actual database connection logic
def get_db_connection():
    # Example for sqlite3, replace with your DB connection
    conn = sqlite3.connect('your_database.db')
    return conn

class EstadoUltimaSolicitudUsuarioInput(BaseModel):
    """Input for estado_ultima_solicitud_usuario tool."""
    dni_usuario: str = Field(..., description="el número de DNI del usuario a consultar")
    nombre_tramite: str = Field(..., description="el nombre exacto del trámite a consultar")

class EstadoUltimaSolicitudUsuarioTool(BaseTool):
    name: str = "estado_ultima_solicitud_usuario"
    description: str = "Consulta el estado actual y la última acción realizada en la solicitud más reciente de un trámite específico para un usuario particular, identificado por su DNI."
    args_schema: Type[BaseModel] = EstadoUltimaSolicitudUsuarioInput

    def _run(self, dni_usuario: str, nombre_tramite: str) -> str:
        query = """
            SELECT 
                u.name AS usuario,
                p.name AS tramite,
                r.start_date AS fecha_inicio,
                r.finish_date AS fecha_fin,
                rs.description AS estado_actual,
                a.description AS ultima_accion,
                ra.created_at AS fecha_accion
            FROM requests r
            JOIN users u ON r.user_id = u.id
            JOIN procedures p ON r.procedure_id = p.id
            JOIN (
                SELECT rsr1.* FROM request_state_records rsr1
                JOIN (
                    SELECT request_id, MAX(date) AS max_date
                    FROM request_state_records GROUP BY request_id
                ) latest ON rsr1.request_id = latest.request_id AND rsr1.date = latest.max_date
            ) rsr ON rsr.request_id = r.id
            JOIN request_states rs ON rs.id = rsr.request_status_id
            LEFT JOIN (
                SELECT ra1.* FROM request_actions ra1
                JOIN (
                    SELECT request_id, MAX(created_at) AS max_date
                    FROM request_actions GROUP BY request_id
                ) latest_ra ON ra1.request_id = latest_ra.request_id AND ra1.created_at = latest_ra.max_date
            ) ra ON ra.request_id = r.id
            LEFT JOIN actions a ON a.id = ra.action_id
            WHERE u.dni = :dni_usuario
              AND p.name = :nombre_tramite
              AND r.id = (
                  SELECT r2.id FROM requests r2
                  JOIN procedures p2 ON r2.procedure_id = p2.id
                  WHERE r2.user_id = u.id
                    AND p2.name = :nombre_tramite
                  ORDER BY r2.created_at DESC
                  LIMIT 1
              )
              AND r.deleted_at IS NULL;
        """
        # --- DATABASE LOGIC NEEDED HERE ---
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # cursor.execute(query, {'dni_usuario': dni_usuario, 'nombre_tramite': nombre_tramite})
        # result = cursor.fetchall()
        # conn.close()
        # return str(result)
        return "Database logic not implemented. Please configure the database connection in src/td_chat/tools/report_tools.py"

class ConteoEstadosTramiteEspecificoInput(BaseModel):
    """Input for conteo_estados_tramite_especifico tool."""
    nombre_tramite: str = Field(..., description="el nombre exacto del trámite que se desea consultar")
    fecha_inicio: str = Field(..., description="la fecha y hora de inicio del período (formato AAAA-MM-DD HH:MM:SS)")
    fecha_fin: str = Field(..., description="la fecha y hora de fin del período (formato AAAA-MM-DD HH:MM:SS)")

class ConteoEstadosTramiteEspecificoTool(BaseTool):
    name: str = "conteo_estados_tramite_especifico"
    description: str = "Entrega un resumen de la cantidad de solicitudes y sus estados finales para un tipo de trámite específico y dentro de un rango de fechas determinado."
    args_schema: Type[BaseModel] = ConteoEstadosTramiteEspecificoInput

    def _run(self, nombre_tramite: str, fecha_inicio: str, fecha_fin: str) -> str:
        query = """
            WITH ultimo_estado AS (
                SELECT r.id AS request_id, p.name AS tramite, rs.description AS estado,
                       ROW_NUMBER() OVER (PARTITION BY r.id ORDER BY rsr.date DESC) AS rn
                FROM requests r
                JOIN procedures p ON r.procedure_id = p.id
                JOIN request_state_records rsr ON rsr.request_id = r.id
                JOIN request_states rs ON rsr.request_status_id = rs.id
                WHERE p.name = :nombre_tramite
                  AND r.start_date BETWEEN :fecha_inicio AND :fecha_fin
                  AND r.deleted_at IS NULL
            )
            SELECT tramite,
                   SUM(CASE WHEN estado = 'Borrador' THEN 1 ELSE 0 END) AS borrador,
                   SUM(CASE WHEN estado = 'Publicado' THEN 1 ELSE 0 END) AS publicado,
                   SUM(CASE WHEN estado = 'En proceso' THEN 1 ELSE 0 END) AS en_proceso,
                   SUM(CASE WHEN estado = 'Finalizado' THEN 1 ELSE 0 END) AS finalizado,
                   SUM(CASE WHEN estado = 'Rechazado' THEN 1 ELSE 0 END) AS rechazado,
                   SUM(CASE WHEN estado = 'Revocado' THEN 1 ELSE 0 END) AS revocado,
                   COUNT(*) AS total
            FROM ultimo_estado WHERE rn = 1 GROUP BY tramite ORDER BY tramite;
        """
        # --- DATABASE LOGIC NEEDED HERE ---
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # cursor.execute(query, {'nombre_tramite': nombre_tramite, 'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin})
        # result = cursor.fetchall()
        # conn.close()
        # return str(result)
        return "Database logic not implemented. Please configure the database connection in src/td_chat/tools/report_tools.py"

class SolicitudesPorEstadoInput(BaseModel):
    """Input for solicitudes_por_estado tool."""
    fecha_inicio: str = Field(..., description="la fecha y hora de inicio del período (formato AAAA-MM-DD HH:MM:SS)")
    fecha_fin: str = Field(..., description="la fecha y hora de fin del período (formato AAAA-MM-DD HH:MM:SS)")

class SolicitudesPorEstadoTool(BaseTool):
    name: str = "solicitudes_por_estado"
    description: str = "Genera un resumen de la cantidad de solicitudes por estado final para CADA tipo de trámite, dentro de un rango de fechas específico."
    args_schema: Type[BaseModel] = SolicitudesPorEstadoInput

    def _run(self, fecha_inicio: str, fecha_fin: str) -> str:
        query = """
            WITH ultimo_estado AS (
                SELECT r.id AS request_id, p.name AS tramite, rs.description AS estado,
                       ROW_NUMBER() OVER (PARTITION BY r.id ORDER BY rsr.date DESC) AS rn
                FROM requests r
                JOIN request_state_records rsr ON rsr.request_id = r.id
                JOIN request_states rs ON rsr.request_status_id = rs.id
                JOIN procedures p ON p.id = r.procedure_id
                WHERE r.created_at BETWEEN :fecha_inicio AND :fecha_fin
                  AND r.deleted_at IS NULL
            )
            SELECT tramite,
                   SUM(CASE WHEN estado = 'Borrador' THEN 1 ELSE 0 END) AS borrador,
                   SUM(CASE WHEN estado = 'Publicado' THEN 1 ELSE 0 END) AS publicado,
                   SUM(CASE WHEN estado = 'En proceso' THEN 1 ELSE 0 END) AS en_proceso,
                   SUM(CASE WHEN estado = 'Finalizado' THEN 1 ELSE 0 END) AS finalizado,
                   SUM(CASE WHEN estado = 'Rechazado' THEN 1 ELSE 0 END) AS rechazado,
                   SUM(CASE WHEN estado = 'Revocado' THEN 1 ELSE 0 END) AS revocado,
                   COUNT(*) AS total
            FROM ultimo_estado WHERE rn = 1 GROUP BY tramite ORDER BY tramite;
        """
        # --- DATABASE LOGIC NEEDED HERE ---
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # cursor.execute(query, {'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin})
        # result = cursor.fetchall()
        # conn.close()
        # return str(result)
        return "Database logic not implemented. Please configure the database connection in src/td_chat/tools/report_tools.py"

class ListAvailableReportsInput(BaseModel):
    """Input for list_available_reports tool."""
    pass

class ListAvailableReportsTool(BaseTool):
    name: str = "list_available_reports"
    description: str = "Use this tool to get a list of the available reports that you can generate."
    args_schema: Type[BaseModel] = ListAvailableReportsInput

    def _run(self) -> str:
        return """
        Available reports:
        1. estado_ultima_solicitud_usuario: Consulta el estado actual y la última acción realizada en la solicitud más reciente de un trámite específico para un usuario particular, identificado por su DNI.
        2. conteo_estados_tramite_especifico: Entrega un resumen de la cantidad de solicitudes y sus estados finales para un tipo de trámite específico y dentro de un rango de fechas determinado.
        3. solicitudes_por_estado: Genera un resumen de la cantidad de solicitudes por estado final para CADA tipo de trámite, dentro de un rango de fechas específico.
        """