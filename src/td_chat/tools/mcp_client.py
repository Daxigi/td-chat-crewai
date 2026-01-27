import os
import asyncio
import nest_asyncio
import time
from typing import List, Any, Optional, Type, Dict
from crewai.tools import BaseTool
from pydantic import PrivateAttr, BaseModel, create_model, Field

from mcp import ClientSession
from mcp.client.sse import sse_client

nest_asyncio.apply()

# --- Configuración ---
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8765/sse")

# --- Caché global ---
_tools_cache: Optional[List[BaseTool]] = None

def _create_dynamic_model(tool_name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    """
    Convierte un esquema JSON (del protocolo MCP) a un modelo Pydantic (para CrewAI).
    Esto permite que el Agente sepa qué argumentos requiere cada herramienta.
    """
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    
    fields = {}
    for field_name, field_info in properties.items():
        field_type = str 
        json_type = field_info.get("type")
        
        if json_type == "integer":
            field_type = int
        elif json_type == "boolean":
            field_type = bool
        elif json_type == "number":
            field_type = float
        elif json_type == "array":
            field_type = List[Any]
        elif json_type == "object":
            field_type = Dict[str, Any]
            
        description = field_info.get("description", "")
        
        if field_name in required_fields:
            fields[field_name] = (field_type, Field(..., description=description))
        else:
            fields[field_name] = (Optional[field_type], Field(None, description=description))
            
    return create_model(f"{tool_name}Input", **fields)

class MCPToolWrapper(BaseTool):
    """
    Wrapper que conecta CrewAI con una herramienta remota MCP.
    """
    name: str
    description: str
    args_schema: Type[BaseModel] 
    _tool_name: str = PrivateAttr()
    _server_url: str = PrivateAttr()

    def __init__(self, name: str, description: str, tool_name: str, server_url: str, args_schema: Type[BaseModel], **kwargs):
        super().__init__(name=name, description=description, args_schema=args_schema, **kwargs)
        self._tool_name = tool_name
        self._server_url = server_url

    def _run(self, **kwargs: Any) -> Any:
        """Método síncrono que llama a la función asíncrona de MCP"""
        
        async def call_remote_mcp():
            print(f"🔌 Ejecutando tool remota: '{self.name}' con args: {kwargs}")
            try:
                async with sse_client(self._server_url) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(self._tool_name, arguments=kwargs)
                        
                        output_text = []
                        if result.content:
                            for content in result.content:
                                if content.type == "text":
                                    output_text.append(content.text)
                                elif content.type == "image":
                                    output_text.append("[Imagen recibida]")
                                elif content.type == "resource":
                                    output_text.append(f"[Recurso: {content.uri}]")
                        
                        final_text = "\n".join(output_text)
                        return final_text
            except Exception as e:
                error_msg = f"❌ Error ejecutando '{self.name}': {str(e)}"
                print(error_msg)
                return error_msg

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return loop.run_until_complete(call_remote_mcp())
            else:
                return asyncio.run(call_remote_mcp())
        except RuntimeError:
            return asyncio.run(call_remote_mcp())

async def _fetch_tools_from_server() -> List[BaseTool]:
    """
    Descubre tools remotas y genera sus esquemas Pydantic.
    Incluye lógica de reintento para robustez inicial.
    """
    print(f"🔄 Iniciando descubrimiento de tools en: {MCP_SERVER_URL}")
    
    max_retries = 3
    retry_delay = 2 

    for attempt in range(max_retries):
        try:
            tools_list = []
            async with sse_client(MCP_SERVER_URL) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.list_tools()
                    
                    for tool in result.tools:
                        dynamic_schema = _create_dynamic_model(tool.name, tool.inputSchema)

                        crew_tool = MCPToolWrapper(
                            name=tool.name,
                            description=tool.description or "Sin descripción.",
                            tool_name=tool.name,
                            server_url=MCP_SERVER_URL,
                            args_schema=dynamic_schema
                        )
                        tools_list.append(crew_tool)
            
            print(f"✅ Se cargaron {len(tools_list)} herramientas desde MCP con sus esquemas.")
            return tools_list

        except Exception as e:
            # Desempaquetar ExceptionGroup si es necesario (común en asyncio TaskGroups)
            if isinstance(e, BaseExceptionGroup):
                errors = e.exceptions
                error_msg = ", ".join([str(err) for err in errors])
            else:
                error_msg = str(e)
            
            print(f"⚠️ Intento {attempt + 1}/{max_retries} fallido al conectar con MCP: {error_msg}")
            
            if "Connection refused" in error_msg or "Cannot connect" in error_msg:
                print("   (💡 Pista: ¿Está el servidor MCP corriendo en el puerto 8000?)")

            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ ERROR CRÍTICO: No se pudo conectar al servidor MCP después de varios intentos.")
                return []
    return []

def get_tools() -> List[BaseTool]:
    """Carga perezosa de tools con caché inteligente."""
    global _tools_cache
    
    # Si ya tenemos herramientas cacheadas, las devolvemos
    if _tools_cache:
        return _tools_cache

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            result = loop.run_until_complete(_fetch_tools_from_server())
        else:
            result = asyncio.run(_fetch_tools_from_server())
    except RuntimeError:
         result = asyncio.run(_fetch_tools_from_server())
    
    # Solo cacheamos si realmente obtuvimos herramientas.
    # Si hubo error (lista vacía), dejamos la caché en None para reintentar luego.
    if result:
        _tools_cache = result
        
    return result

class LazyToolLoader:
    def __iter__(self):
        return iter(get_tools())
    def __len__(self):
        return len(get_tools())
    def __getitem__(self, item):
        return get_tools()[item]

tools = LazyToolLoader()
