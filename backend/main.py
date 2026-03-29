# =============================================================================
# main.py - Servidor Backend del Validador KYC
# =============================================================================
# Este archivo es el "cerebro" de la aplicacion. Recibe dos imagenes
# (una INE/identificacion y una selfie), las compara usando IA para
# determinar si son la misma persona, y extrae el texto visible.
#
# Enfoque hibrido de privacidad:
#   - Deteccion de rostros: LOCAL (OpenCV DNN) - nada sale de tu computadora
#   - Extraccion de texto:  LOCAL (EasyOCR) - nada sale de tu computadora
#   - Comparacion facial:   OpenRouter/Gemini - solo se envian recortes de rostro
#                           (sin datos personales, sin texto de la INE)
#
# Tecnologias:
#   - FastAPI: Framework web rapido para crear la API REST
#   - OpenCV DNN: Deteccion y recorte de rostros (local, sin GPU)
#   - EasyOCR: Extraccion de texto de la identificacion (local)
#   - OpenRouter + Gemini: Comparacion facial (solo recortes de rostro)
#
# Para correr en local:
#   python main.py
# =============================================================================

import os
import io
import base64
import json
import urllib.request

import cv2
import numpy as np
import easyocr
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
    version="3.0.0"
)

# -----------------------------------------------------------------------------
# 2. CONFIGURACION DE CORS
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 4. CARGA DE MODELOS LOCALES
# -----------------------------------------------------------------------------
# 4a. Detector de rostros OpenCV DNN (SSD basado en ResNet-10)
# Detecta rostros con alta precision sin necesidad de GPU ni TensorFlow.
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
face_net = cv2.dnn.readNetFromCaffe(
    os.path.join(MODELS_DIR, "deploy.prototxt"),
    os.path.join(MODELS_DIR, "res10_300x300_ssd_iter_140000.caffemodel")
)
print("Modelo de deteccion facial cargado (OpenCV DNN).")

# 4b. EasyOCR para extraccion de texto (local, usa PyTorch)
print("Cargando modelo OCR EasyOCR (idioma: espanol)...")
lector_ocr = easyocr.Reader(['es'], gpu=False)
print("Modelo OCR cargado exitosamente.")

# -----------------------------------------------------------------------------
# 5. FUNCIONES AUXILIARES
# -----------------------------------------------------------------------------

def bytes_a_imagen(contenido: bytes) -> np.ndarray:
    """Convierte bytes de un archivo de imagen a un array OpenCV (BGR)."""
    arr = np.frombuffer(contenido, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("No se pudo decodificar la imagen")
    return img


def detectar_rostro_principal(img: np.ndarray, min_confianza: float = 0.5) -> np.ndarray:
    """
    Detecta todos los rostros en la imagen usando OpenCV DNN y retorna
    el recorte del rostro mas grande (mayor area en pixeles).

    Esto es clave para la INE: tiene una foto principal (grande, color)
    y una foto fantasma (pequena, gris). Siempre tomamos la mas grande.
    """
    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(img, 1.0, (300, 300), (104.0, 177.0, 123.0))
    face_net.setInput(blob)
    detecciones = face_net.forward()

    rostros = []
    for i in range(detecciones.shape[2]):
        confianza = detecciones[0, 0, i, 2]
        if confianza > min_confianza:
            box = detecciones[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            # Clamp a los limites de la imagen
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            area = (x2 - x1) * (y2 - y1)
            if area > 0:
                rostros.append((x1, y1, x2, y2, area))

    if not rostros:
        raise ValueError("No se detecto ningun rostro en la imagen")

    # Tomar el rostro mas grande
    x1, y1, x2, y2, _ = max(rostros, key=lambda r: r[4])

    # Agregar padding del 20% para incluir mas contexto facial
    pad_w = int(0.2 * (x2 - x1))
    pad_h = int(0.2 * (y2 - y1))
    x1 = max(0, x1 - pad_w)
    y1 = max(0, y1 - pad_h)
    x2 = min(w, x2 + pad_w)
    y2 = min(h, y2 + pad_h)

    return img[y1:y2, x1:x2]


def imagen_a_base64(img: np.ndarray) -> str:
    """Codifica un array OpenCV (BGR) a base64 JPEG."""
    _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buffer).decode()


def llamar_openrouter(prompt: str, imagenes_b64: list[str]) -> dict:
    """
    Envia un prompt con imagenes a OpenRouter y retorna la respuesta parseada.
    NOTA: en esta version solo se envian recortes de rostro, no la INE completa.
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
# Flujo de privacidad:
#   1. Recibe INE + selfie
#   2. LOCAL: OpenCV detecta y recorta el rostro principal de cada imagen
#   3. LOCAL: EasyOCR extrae el texto de la INE completa
#   4. REMOTO: Solo los recortes de rostro se envian a Gemini para comparar
#   -> Ningun dato personal (nombre, CURP, direccion) sale de tu computadora

PROMPT_COMPARACION = """Analiza estas dos fotos de rostros. La primera es un recorte de una identificacion oficial y la segunda es una selfie.

Determina si es la misma persona comparando rasgos faciales.

Responde UNICAMENTE con un JSON valido con esta estructura exacta:
{"misma_persona": true/false, "similitud": 0-100}

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
        # --- Paso 1: Leer imagenes en memoria ---
        ine_bytes = await ine.read()
        selfie_bytes = await selfie.read()

        ine_img = bytes_a_imagen(ine_bytes)
        selfie_img = bytes_a_imagen(selfie_bytes)

        # --- Paso 2 (LOCAL): Recortar el rostro principal de cada imagen ---
        # Solo el recorte del rostro saldra de tu computadora
        rostro_ine = detectar_rostro_principal(ine_img)
        rostro_selfie = detectar_rostro_principal(selfie_img)

        # --- Paso 3 (LOCAL): Extraer texto de la INE con EasyOCR ---
        # La imagen completa de la INE NUNCA se envia a ningun servicio externo
        textos = lector_ocr.readtext(ine_img, detail=0)
        texto_extraido = "\n".join(textos) if textos else "No se encontro texto"

        # --- Paso 4 (REMOTO): Comparar rostros via Gemini ---
        # Solo se envian los recortes de rostro (sin texto, sin datos personales)
        rostro_ine_b64 = imagen_a_base64(rostro_ine)
        rostro_selfie_b64 = imagen_a_base64(rostro_selfie)

        resultado = llamar_openrouter(PROMPT_COMPARACION, [rostro_ine_b64, rostro_selfie_b64])

        return {
            "misma_persona": resultado.get("misma_persona", False),
            "similitud": resultado.get("similitud", 0),
            "texto_extraido": texto_extraido
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
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
