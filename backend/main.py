# =============================================================================
# main.py - Servidor Backend del Validador KYC
# =============================================================================
# Este archivo es el "cerebro" de la aplicacion. Recibe dos imagenes
# (una INE/identificacion y una selfie), las compara usando IA para
# determinar si son la misma persona, y extrae el texto visible.
#
# Tecnologias:
#   - FastAPI: Framework web rapido para crear la API REST
#   - OpenRouter + Gemini: API de vision para comparacion facial y OCR
#
# Para correr en local:
#   python main.py
#
# Railway inyecta la variable PORT automaticamente al desplegar.
# =============================================================================

import os
import base64
import json
import urllib.request

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------------------------------
# 1. CONFIGURACION DE LA APP
# -----------------------------------------------------------------------------
app = FastAPI(
    title="KYC Validador de Identidad",
    description="API para verificacion facial y extraccion de texto (OCR)",
    version="2.0.0"
)

# -----------------------------------------------------------------------------
# 2. CONFIGURACION DE CORS
# -----------------------------------------------------------------------------
# CORS permite que el frontend (React) se comunique con este backend.
# La variable ALLOWED_ORIGINS se configura en .env:
#   - Local: http://localhost:5173
#   - Produccion: https://tu-frontend.railway.app
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# 3. CONFIGURACION DE OPENROUTER
# -----------------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

if not OPENROUTER_API_KEY:
    print("ADVERTENCIA: No se encontro OPENROUTER_API_KEY en las variables de entorno.")
    print("Configura tu API key en el archivo .env")

# -----------------------------------------------------------------------------
# 4. FUNCION AUXILIAR: Convertir UploadFile a base64
# -----------------------------------------------------------------------------
async def archivo_a_base64(archivo: UploadFile) -> str:
    """Lee un archivo subido y lo convierte a base64 para enviarlo a la API."""
    contenido = await archivo.read()
    return base64.b64encode(contenido).decode()

# -----------------------------------------------------------------------------
# 5. FUNCION AUXILIAR: Llamar a OpenRouter con imagenes
# -----------------------------------------------------------------------------
def llamar_openrouter(prompt: str, imagenes_b64: list[str]) -> dict:
    """
    Envia un prompt con imagenes a OpenRouter y retorna la respuesta parseada.
    Las imagenes se envian como base64 en formato OpenAI-compatible.
    """
    content = [{"type": "text", "text": prompt}]
    for img in imagenes_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img}"}
        })

    body = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
    }).encode()

    req = urllib.request.Request(OPENROUTER_URL, data=body, headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    })

    resp = urllib.request.urlopen(req, timeout=60)
    data = json.loads(resp.read())
    respuesta_texto = data["choices"][0]["message"]["content"]

    # Gemini a veces envuelve el JSON en ```json ... ```, lo limpiamos
    respuesta_texto = respuesta_texto.strip()
    if respuesta_texto.startswith("```"):
        respuesta_texto = respuesta_texto.split("\n", 1)[1]
        respuesta_texto = respuesta_texto.rsplit("```", 1)[0]

    return json.loads(respuesta_texto)

# -----------------------------------------------------------------------------
# 6. ENDPOINT PRINCIPAL: /api/verificar
# -----------------------------------------------------------------------------
# Recibe dos imagenes via POST (multipart/form-data):
#   - ine: Foto de la identificacion oficial (INE, pasaporte, etc.)
#   - selfie: Foto selfie de la persona
#
# Envia ambas imagenes a Gemini en una sola llamada para:
#   1. Comparar los rostros y determinar si es la misma persona
#   2. Extraer el texto visible de la identificacion (OCR)
PROMPT_VERIFICACION = """Analiza estas dos imagenes. La primera es una identificacion oficial (INE/pasaporte) y la segunda es una selfie de una persona.

Realiza estas dos tareas:

1. COMPARACION FACIAL: Compara el rostro de la identificacion con el rostro de la selfie. La identificacion puede tener una foto principal (grande, a color) y una foto fantasma (pequena, gris). Usa la foto principal para comparar.

2. EXTRACCION DE TEXTO: Extrae todo el texto visible de la identificacion (nombres, CURP, clave de elector, direccion, etc.).

Responde UNICAMENTE con un JSON valido con esta estructura exacta:
{"misma_persona": true/false, "similitud": 0-100, "texto_extraido": "todo el texto encontrado separado por saltos de linea"}

No agregues explicaciones, solo el JSON."""

@app.post("/api/verificar")
async def verificar_identidad(
    ine: UploadFile = File(..., description="Imagen de la identificacion oficial"),
    selfie: UploadFile = File(..., description="Imagen selfie de la persona")
):
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="No se configuro OPENROUTER_API_KEY. Agrega tu API key en el archivo .env"
        )

    try:
        # Paso 1: Convertir imagenes a base64
        ine_b64 = await archivo_a_base64(ine)
        selfie_b64 = await archivo_a_base64(selfie)

        # Paso 2: Enviar a Gemini via OpenRouter (comparacion facial + OCR en una llamada)
        resultado = llamar_openrouter(PROMPT_VERIFICACION, [ine_b64, selfie_b64])

        return {
            "misma_persona": resultado.get("misma_persona", False),
            "similitud": resultado.get("similitud", 0),
            "texto_extraido": resultado.get("texto_extraido", "No se encontro texto")
        }

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"La IA retorno una respuesta no valida: {str(e)}"
        )
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        raise HTTPException(
            status_code=502,
            detail=f"Error al comunicarse con OpenRouter: {error_body}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar las imagenes: {str(e)}"
        )

# -----------------------------------------------------------------------------
# 7. ENDPOINT DE SALUD (Health Check)
# -----------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "servicio": "KYC Validador de Identidad", "modelo": OPENROUTER_MODEL}

# -----------------------------------------------------------------------------
# 8. ARRANQUE DEL SERVIDOR
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Iniciando servidor en http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
