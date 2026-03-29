# =============================================================================
# Dockerfile - Backend Python (FastAPI + DeepFace + EasyOCR)
# =============================================================================
# Este Dockerfile construye la imagen del backend para Railway.
# Usa Python 3.11 slim para reducir el tamano base de la imagen.
# =============================================================================

# Imagen base ligera de Python
FROM python:3.11-slim

# Instalar dependencias del sistema que necesitan OpenCV y las librerias de IA
# libgl1 y libglib2.0-0 son necesarias para opencv-python-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar solo requirements.txt primero para aprovechar el cache de Docker
# Si requirements.txt no cambia, Docker reutiliza esta capa sin reinstalar
COPY requirements.txt .

# Instalar dependencias de Python
# --no-cache-dir evita guardar cache de pip (reduce tamano de imagen)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el codigo fuente de la aplicacion
COPY . .

# Puerto que expone el contenedor (Railway inyecta PORT como variable de entorno)
EXPOSE 8000

# Comando para arrancar el servidor
# $PORT es inyectado por Railway; si no existe, usa 8000 por defecto
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
