FROM python:3.12-slim

# Configuración básica
WORKDIR /app

# 1. Copiamos los archivos de definición del proyecto
# Es importante copiar README.md si tu pyproject.toml lo referencia
COPY pyproject.toml README.md ./

# 2. Copiamos el código fuente (NECESARIO para que pip instale el paquete)
COPY src ./src

# 3. Instalamos las dependencias y el propio proyecto
# Esto lee [project.dependencies] o [tool.poetry.dependencies] y instala todo (incluyendo mem0ai)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir .

# 4. Copiamos el resto de los archivos (como app.py, archivos de config, etc.)
COPY . .

# Exponemos el puerto que usas
EXPOSE 8876

# Ejecutamos la aplicación
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8876"]