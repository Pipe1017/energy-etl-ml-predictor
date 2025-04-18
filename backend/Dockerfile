# backend/Dockerfile

# Usa una imagen oficial de Python como base
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos ANTES de copiar el resto del código
# Esto aprovecha el cache de Docker si los requerimientos no cambian
COPY requirements.txt requirements.txt

# Instala las dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación al directorio de trabajo
COPY . .

# Expone el puerto en el que Uvicorn se ejecutará dentro del contenedor
EXPOSE 8000

# Comando para ejecutar la aplicación cuando el contenedor se inicie
# Escucha en 0.0.0.0 para ser accesible desde fuera del contenedor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]