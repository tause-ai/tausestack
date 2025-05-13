FROM python:3.11-slim

WORKDIR /app

# Copiar primero los requisitos para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Instalación del framework TauseStack
# Nota: En un proyecto real, se debería instalar desde PyPI o un repositorio Git
COPY services /app/services/

# Copiar el código de la aplicación
COPY app /app/app/
COPY .env .env

# Puerto por defecto para FastAPI
EXPOSE 8000

# Comando para iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
