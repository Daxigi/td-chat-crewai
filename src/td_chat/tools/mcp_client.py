import requests
from typing import List, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, create_model
import os

# --- Configuración del Cliente MCP ---
# Es una buena práctica leer la URL del servidor desde variables de entorno
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

def load_tools_from_mcp() -> List[BaseTool]:
    """
    Carga dinámicamente las herramientas desde un servidor MCP y las convierte
    en herramientas compatibles con CrewAI.

    Esta función se conecta al endpoint /tools del servidor MCP, obtiene la
    definición de cada herramienta y crea una clase de herramienta de CrewAI
    dinámicamente que sabe cómo ejecutar la herramienta remota.
    """
    print(f"Cargando herramientas desde el servidor MCP en: {MCP_SERVER_URL}")
    try:
        # 1. Obtener la lista de herramientas del servidor MCP
        response = requests.get(f"{MCP_SERVER_URL}/tools")
        response.raise_for_status()  # Lanza un error si la petición falla
        remote_tools_schemas = response.json()
        print(f"Se encontraron {len(remote_tools_schemas)} herramientas en el servidor.")

        # 2. Crear dinámicamente herramientas de CrewAI para cada herramienta remota
        crewai_tools: List[BaseTool] = []
        for tool_schema in remote_tools_schemas:
            tool_name = tool_schema['name']
            tool_description = tool_schema['description']

            # Crear el esquema de argumentos Pydantic dinámicamente
            args_fields = {}
            if 'properties' in tool_schema.get('args_schema', {}):
                for prop_name, prop_details in tool_schema['args_schema']['properties'].items():
                    # Mapeo simple de tipos de JSON Schema a Python.
                    # Se puede extender si usas tipos más complejos (int, bool, etc.)
                    field_type = str
                    args_fields[prop_name] = (field_type, Field(..., description=prop_details.get('description')))

            DynamicArgsSchema = create_model(f"{tool_name}Input", **args_fields)

            # --- Función de ejecución para la herramienta dinámica ---
            # Esta función será el corazón de nuestra herramienta dinámica.
            # Sabe cómo llamar al servidor MCP para ejecutar la herramienta real.
            def _run_mcp_tool(self, **kwargs) -> str:
                tool_to_run = self.name
                print(f"Ejecutando herramienta remota '{tool_to_run}' con argumentos: {kwargs}")
                try:
                    exec_response = requests.post(
                                                f"{MCP_SERVER_URL}/tools/execute",
                        json={"tool_name": tool_to_run, "args": kwargs}
                    )
                    exec_response.raise_for_status()
                    result = exec_response.json().get("result", "La herramienta no devolvió resultado.")
                    print(f"Resultado de '{tool_to_run}': {result}")
                    return result
                except requests.exceptions.RequestException as e:
                    error_message = f"Error al ejecutar la herramienta remota '{tool_to_run}': {e}"
                    print(error_message)
                    return error_message

            # Crear una nueva clase de herramienta para cada herramienta remota
            ToolClass = type(
                tool_name,
                (BaseTool,),
                {
                    "name": tool_name,
                    "description": tool_description,
                    "args_schema": DynamicArgsSchema,
                    "_run": _run_mcp_tool
                }
            )
            crewai_tools.append(ToolClass())

        return crewai_tools

    except requests.exceptions.RequestException as e:
        print(f"ERROR: No se pudieron cargar las herramientas desde el servidor MCP. Asegúrate de que el servidor esté corriendo en {MCP_SERVER_URL}. Detalle: {e}")
        return []