# =============================================================================
# main.py - Servidor Backend del Validador KYC
# =============================================================================
# Enfoque hibrido de privacidad con doble verificacion:
#   - Deteccion de rostros: LOCAL (OpenCV DNN)
#   - Extraccion de texto:  LOCAL (EasyOCR)
#   - Comparacion facial:   REMOTO (doble verificacion: gpt-4o-mini + gemini-2.5-flash)
#                           Solo se envian recortes de rostro (~100-200KB)
#                           Ningun dato personal sale de tu computadora
#
# Para correr en local:
#   python main.py
# =============================================================================

import os
import base64
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor

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
    version="3.1.0"
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
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Doble verificacion: dos modelos que fallan en casos diferentes
MODELO_1 = "openai/gpt-4o-mini"
MODELO_2 = "google/gemini-2.5-flash"

if not OPENROUTER_API_KEY:
    print("ADVERTENCIA: No se encontro OPENROUTER_API_KEY en las variables de entorno.")

# -----------------------------------------------------------------------------
# 4. CARGA DE MODELOS LOCALES
# -----------------------------------------------------------------------------
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
face_net = cv2.dnn.readNetFromCaffe(
    os.path.join(MODELS_DIR, "deploy.prototxt"),
    os.path.join(MODELS_DIR, "res10_300x300_ssd_iter_140000.caffemodel")
)
print("Modelo de deteccion facial cargado (OpenCV DNN).")

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
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            area = (x2 - x1) * (y2 - y1)
            if area > 0:
                rostros.append((x1, y1, x2, y2, area))

    if not rostros:
        raise ValueError("No se detecto ningun rostro en la imagen")

    x1, y1, x2, y2, _ = max(rostros, key=lambda r: r[4])

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


def llamar_openrouter(modelo: str, prompt: str, imagenes_b64: list[str]) -> dict:
    """
    Envia un prompt con imagenes a un modelo especifico via OpenRouter.
    NOTA: solo se envian recortes de rostro, no la INE completa.
    """
    content = [{"type": "text", "text": prompt}]
    for img in imagenes_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img}"}
        })

    body = json.dumps({
        "model": modelo,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
    }).encode()

    req = urllib.request.Request(OPENROUTER_URL, data=body, headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    })

    resp = urllib.request.urlopen(req, timeout=90)
    data = json.loads(resp.read())
    respuesta_texto = data["choices"][0]["message"]["content"]

    respuesta_texto = respuesta_texto.strip()
    if respuesta_texto.startswith("```"):
        respuesta_texto = respuesta_texto.split("\n", 1)[1]
        respuesta_texto = respuesta_texto.rsplit("```", 1)[0]

    return json.loads(respuesta_texto)

# -----------------------------------------------------------------------------
# 6. ENDPOINT PRINCIPAL: /api/verificar
# -----------------------------------------------------------------------------
# Flujo:
#   1. LOCAL: OpenCV recorta el rostro principal de INE y selfie
#   2. LOCAL: EasyOCR extrae texto de la INE
#   3. REMOTO: Solo los recortes de rostro se envian a dos modelos en paralelo
#   4. Doble verificacion: ambos deben aprobar
#   -> Ningun dato personal sale de tu computadora

PROMPT_COMPARACION = """Compara los rostros en estas dos fotos analizando unicamente la estructura osea y rasgos permanentes:
- Forma del craneo y proporcion de la frente
- Estructura de pomulos y mandibula
- Forma y tamano de la nariz (puente, punta, aletas)
- Distancia entre los ojos y su forma
- Forma de los labios
- Proporcion general del rostro (redondo, ovalado, cuadrado, alargado)

No consideres: lentes, vello facial, peinado, maquillaje, peso, iluminacion ni angulo de la foto. Dos personas pueden verse parecidas por usar lentes similares o tener barba parecida, pero eso no significa que sean la misma persona.

Si tienes duda, responde false.

Responde solo con JSON:
{"misma_persona": true/false, "similitud": 0-100, "explicacion": "una frase breve explicando las coincidencias o diferencias clave encontradas"}"""

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
        # Paso 1 (LOCAL): Leer imagenes
        ine_bytes = await ine.read()
        selfie_bytes = await selfie.read()
        ine_img = bytes_a_imagen(ine_bytes)
        selfie_img = bytes_a_imagen(selfie_bytes)

        # Paso 2 (LOCAL): Recortar el rostro principal de cada imagen
        rostro_ine = detectar_rostro_principal(ine_img)
        rostro_selfie = detectar_rostro_principal(selfie_img)

        # Paso 3 (LOCAL): Extraer texto de la INE con EasyOCR
        textos = lector_ocr.readtext(ine_img, detail=0)
        texto_extraido = "\n".join(textos) if textos else "No se encontro texto"

        # Paso 4 (REMOTO): Comparar rostros con doble verificacion
        rostro_ine_b64 = imagen_a_base64(rostro_ine)
        rostro_selfie_b64 = imagen_a_base64(rostro_selfie)
        imagenes = [rostro_ine_b64, rostro_selfie_b64]

        with ThreadPoolExecutor(max_workers=2) as executor:
            futuro_1 = executor.submit(llamar_openrouter, MODELO_1, PROMPT_COMPARACION, imagenes)
            futuro_2 = executor.submit(llamar_openrouter, MODELO_2, PROMPT_COMPARACION, imagenes)
            resultado_1 = futuro_1.result()
            resultado_2 = futuro_2.result()

        # Paso 5: Doble verificacion - ambos deben aprobar
        match_1 = resultado_1.get("misma_persona", False)
        match_2 = resultado_2.get("misma_persona", False)
        sim_1 = resultado_1.get("similitud", 0)
        sim_2 = resultado_2.get("similitud", 0)

        misma_persona = match_1 and match_2
        similitud = round((sim_1 + sim_2) / 2)

        # Construir explicacion
        exp_1 = resultado_1.get("explicacion", "")
        exp_2 = resultado_2.get("explicacion", "")
        if match_1 != match_2:
            explicacion = f"Resultado parcial: un modelo aprueba y otro rechaza. {exp_1 or exp_2}"
        else:
            explicacion = exp_1 if len(exp_1) >= len(exp_2) else exp_2

        return {
            "misma_persona": misma_persona,
            "similitud": similitud,
            "explicacion": explicacion or "",
            "texto_extraido": texto_extraido,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    return {
        "status": "ok",
        "servicio": "KYC Validador de Identidad",
        "modelos": [MODELO_1, MODELO_2],
        "verificacion": "doble",
        "procesamiento_local": ["deteccion_rostros", "ocr"]
    }

# -----------------------------------------------------------------------------
# 8. ARRANQUE DEL SERVIDOR
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Iniciando servidor en http://0.0.0.0:{port}")
    print(f"Doble verificacion: {MODELO_1} + {MODELO_2}")
    print("Procesamiento local: deteccion de rostros (OpenCV) + OCR (EasyOCR)")
    uvicorn.run(app, host="0.0.0.0", port=port)
