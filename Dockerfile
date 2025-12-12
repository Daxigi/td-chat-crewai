FROM python:3.12-slim

# 1. Instalar poetry
RUN pip install poetry

# 2. Configurar el entorno de Poetry para que no cree entornos virtuales dentro del contenedor
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

# 3. Establecer el directorio de trabajo
WORKDIR /app

# 4. Copiar solo los archivos de dependencias primero para optimizar el cache de Docker
COPY pyproject.toml poetry.lock ./

# 5. Instalar dependencias usando poetry.lock. Se omiten las de desarrollo.
RUN poetry install --no-root

# 6. Copiar el resto del código de la aplicación
COPY . .

# 7. Exponer el puerto correcto
EXPOSE 8765

# 8. Ejecutar la aplicación
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8765"]

