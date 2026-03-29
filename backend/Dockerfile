# =============================================================================
# Dockerfile - Backend Python (FastAPI + OpenCV DNN + EasyOCR)
# =============================================================================
# Imagen del backend con procesamiento local de rostros y OCR.
# Usa Python 3.11 slim para reducir el tamano base.
# =============================================================================

FROM python:3.11-slim

# Dependencias del sistema para OpenCV y EasyOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python (cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo fuente y modelos
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
