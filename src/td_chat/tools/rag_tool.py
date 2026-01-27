from crewai_tools import MDXSearchTool
from crewai.tools import tool

# Usamos MDXSearchTool para RAG real.
# Esta herramienta entiende la estructura Markdown (## Títulos) y hace chunks inteligentes.
_internal_rag_tool = MDXSearchTool(
    mdx='knowledge/tramites_municipales_expanded.md',
    config={
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini",
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
            },
        },
    }
)

@tool("Buscador de Trámites")
def tramites_rag_tool(query: str) -> str:
    """
    Busca información específica en la Guía de Trámites Municipales.
    Usa esta herramienta para encontrar requisitos, costos, plazos y lugares de atención.
    """
    # Ahora sí usamos el query para traer SOLO los chunks relevantes (RAG)
    return _internal_rag_tool.run(query)
