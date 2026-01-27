# Usamos una imagen base ligera y moderna de Python
FROM python:3.12-slim-bookworm

# --- INSTALACIÓN DE UV ---
# Copiamos el binario de uv directamente desde su imagen oficial (Patrón Best Practice)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# --- CONFIGURACIÓN DE UV ---
# 1. Compilar bytecode para arranque más rápido
# 2. Modo de enlace copia (mejor compatibilidad en Docker)
# 3. Definimos dónde se creará el entorno virtual (.venv)
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT="/app/.venv"

WORKDIR /app

# --- INSTALACIÓN DE DEPENDENCIAS ---
# Copiamos primero los archivos de definición para aprovechar el caché de capas de Docker
COPY pyproject.toml uv.lock ./

# Instalamos las dependencias.
# --frozen: Usa exactamente las versiones del uv.lock (seguridad)
# --no-install-project: No instala tu código todavía, solo librerías
RUN uv sync --frozen --no-install-project

# --- CÓDIGO DE LA APP ---
COPY . .

# Agregamos el entorno virtual al PATH para que 'python' sea el del venv
ENV PATH="/app/.venv/bin:$PATH"
# Agregamos src al PYTHONPATH por si tienes imports absolutos
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# --- EJECUCIÓN ---
# Si tu bot usa Polling (lo normal), se ejecuta como script:
CMD ["python", "src/main.py"]

# NOTA: Si realmente necesitas Uvicorn (porque usas Webhooks), descomenta la siguiente línea y comenta la anterior:
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8765"]