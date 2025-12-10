import os
import requests
from typing import List, Type, Dict, Any, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, create_model

# --- Configuración del Cliente MCP ---
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8765")

# --- Caché para Carga Perezosa (Lazy Loading) ---
_tools_cache: Optional[List[BaseTool]] = None

def get_tools() -> List[BaseTool]:
    """
    Carga y devuelve las herramientas desde el servidor MCP, usando una caché
    para evitar recargas. La carga es perezosa (lazy), ocurre solo la
    primera vez que se llama a esta función.
    """
    global _tools_cache
    if _tools_cache is not None:
        return _tools_cache

    print(f"Iniciando carga perezosa de herramientas desde: {MCP_SERVER_URL}")
    _tools_cache = []  # Inicializar caché para evitar reintentos en caso de error
    try:
        # 1. Obtener la lista de herramientas del servidor MCP
        response = requests.get(f"{MCP_SERVER_URL}/tools", timeout=15)
        response.raise_for_status()
        remote_tools_schemas = response.json()
        print(f"Se encontraron {len(remote_tools_schemas)} herramientas en el servidor.")

        # 2. Crear dinámicamente herramientas de CrewAI
        for tool_schema in remote_tools_schemas:
            tool_name = tool_schema.get('name')
            tool_description = tool_schema.get('description')

            if not tool_name or not tool_description:
                print(f"ADVERTENCIA: Esquema de herramienta inválido (falta nombre o descripción): {tool_schema}")
                continue

            # Crear esquema de argumentos Pydantic dinámicamente
            args_fields = {}
            if 'properties' in tool_schema.get('args_schema', {}):
                for prop_name, prop_details in tool_schema['args_schema']['properties'].items():
                    field_type = str  # Asumimos string, se puede extender
                    args_fields[prop_name] = (field_type, Field(..., description=prop_details.get('description')))

            DynamicArgsSchema = create_model(f"{tool_name}Input", **args_fields)

            # Función de ejecución para la herramienta dinámica
            def _run_mcp_tool(self, **kwargs) -> str:
                # Usamos self.name para obtener el nombre de la herramienta en tiempo de ejecución
                tool_to_run = self.name
                print(f"Ejecutando herramienta remota '{tool_to_run}' con argumentos: {kwargs}")
                try:
                    exec_response = requests.post(
                        f"{MCP_SERVER_URL}/tools/execute",
                        json={"tool_name": tool_to_run, "args": kwargs},
                        timeout=30
                    )
                    exec_response.raise_for_status()
                    result = exec_response.json().get("result", f"La herramienta '{tool_to_run}' no devolvió resultado.")
                    print(f"Resultado de '{tool_to_run}': {result}")
                    return result
                except requests.exceptions.RequestException as e:
                    error_message = f"Error al ejecutar la herramienta remota '{tool_to_run}': {e}"
                    print(error_message)
                    return error_message

            # Crear la clase de la herramienta dinámicamente
            ToolClass = type(
                tool_name,
                (BaseTool,),
                {
                    "__module__": __name__,
                    "__annotations__": {
                        "name": str,
                        "description": str,
                        "args_schema": Type[BaseModel]
                    },
                    "name": tool_name,
                    "description": tool_description,
                    "args_schema": DynamicArgsSchema,
                    "_run": _run_mcp_tool
                }
            )
            _tools_cache.append(ToolClass())
        
        print(f"Carga perezosa completada. {len(_tools_cache)} herramientas listas.")
        return _tools_cache

    except requests.exceptions.RequestException as e:
        print(f"ERROR (lazy load): No se pudieron cargar las herramientas desde el MCP. Detalle: {e}")
        return _tools_cache  # Devuelve la caché vacía
    except Exception as e:
        print(f"ERROR (lazy load): Ocurrió un error inesperado. Detalle: {e}")
        return _tools_cache # Devuelve la caché vacía

# --- Interfaz Pública para el Módulo ---

class LazyToolLoader:
    """
    Clase que permite que la variable 'tools' sea iterable y se comporte como
    una lista, pero disparando la carga perezosa solo cuando se accede a ella.
    """
    def __iter__(self):
        return iter(get_tools())
    def __len__(self):
        return len(get_tools())
    def __getitem__(self, item):
        return get_tools()[item]

# La variable 'tools' ahora es una instancia de nuestro cargador perezoso.
# El código que la importe puede iterar sobre ella (p. ej. `for tool in tools:`),
# y la función `get_tools()` solo se llamará en ese momento.
tools = LazyToolLoader()

# Función de compatibilidad por si alguna parte del código antiguo la llama directamente
def load_tools_from_mcp() -> List[BaseTool]:
    return get_tools()