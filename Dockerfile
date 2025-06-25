# 1. Usar una imagen base de Python slim
FROM python:3.11-slim

# 2. Establecer variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Instalar dependencias
# Copiar primero el archivo de requisitos para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el código de la aplicación
# Copiamos el directorio 'tausestack' que contiene nuestro código fuente
COPY ./tausestack ./tausestack

# 6. Exponer el puerto en el que se ejecuta la aplicación
EXPOSE 8000

# 7. Definir el comando para ejecutar la aplicación
CMD ["uvicorn", "tausestack.framework.main:app", "--host", "0.0.0.0", "--port", "8000"]
