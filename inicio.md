Aquí tienes tu plan de acción completo y estructurado. Esta es tu guía definitiva para construir el MVP de tu validador KYC (Know Your Customer) en local, separando el "Cerebro" (Backend) de la "Cara" (Frontend) y añadiendo **Tailwind CSS** para que tu herramienta interna luzca moderna y profesional desde el día uno.

---

## 🚀 Plan de Acción: MVP Validador de Identidad (React + Python)

Este sistema funciona con dos motores corriendo en paralelo en tu computadora. Uno procesa la Inteligencia artificial y el otro muestra la interfaz.

### Fase 1: El Backend (Cerebro en Python + FastAPI)

Este será el motor que recibe las fotos, ejecuta los modelos matemáticos y devuelve los resultados.

**1. Preparar el entorno:**
Abre tu terminal en la carpeta raíz donde vivirá todo tu proyecto y ejecuta:
```bash
# Crea una carpeta para tu proyecto y entra en ella
mkdir kyc-project
cd kyc-project

# Crea y activa el entorno virtual de Python
python -m venv backend_env
# En Windows: backend_env\Scripts\activate
# En Mac/Linux: source backend_env/bin/activate
```

**2. Instalar las dependencias de IA y Servidor:**
```bash
pip install fastapi uvicorn python-multipart deepface easyocr opencv-python tf-keras
```

**3. Crear el servidor (API):**
Dentro de tu carpeta `kyc-project`, crea un archivo llamado `main.py` y pega el motor principal:

```python
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from deepface import DeepFace
import easyocr
import shutil
import os

app = FastAPI()

# Permite que React (Frontend) se comunique con Python (Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Cargando modelo OCR EasyOCR...")
lector_ocr = easyocr.Reader(['es'], gpu=False)

@app.post("/api/verificar")
async def verificar_identidad(ine: UploadFile = File(...), selfie: UploadFile = File(...)):
    ine_path = f"temp_{ine.filename}"
    selfie_path = f"temp_{selfie.filename}"

    # Guardar imágenes temporalmente
    with open(ine_path, "wb") as buffer: shutil.copyfileobj(ine.file, buffer)
    with open(selfie_path, "wb") as buffer: shutil.copyfileobj(selfie.file, buffer)

    try:
        # 1. Reconocimiento Facial
        resultado_facial = DeepFace.verify(
            img1_path=ine_path, img2_path=selfie_path,
            model_name="Facenet512", enforce_detection=True
        )
        distancia = resultado_facial['distance']
        umbral = resultado_facial['threshold']
        porcentaje = max(0.0, min(100.0, (1 - (distancia / (umbral * 2))) * 100))

        # 2. Extracción de Texto
        textos_encontrados = lector_ocr.readtext(selfie_path, detail=0)
        texto_unido = "\n".join(textos_encontrados) if textos_encontrados else "No se encontró texto"

        return {
            "misma_persona": resultado_facial['verified'],
            "similitud": round(porcentaje, 2),
            "texto_extraido": texto_unido
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        # Limpieza de archivos
        if os.path.exists(ine_path): os.remove(ine_path)
        if os.path.exists(selfie_path): os.remove(selfie_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**4. Arrancar el Backend:**
Ejecuta el servidor y déjalo corriendo en esa ventana de la terminal:
```bash
python main.py
```

---

### Fase 2: El Frontend (Interfaz en React + Vite + Tailwind CSS)

Esta será la plataforma visual que usarás en tu día a día para procesar tus 10 peticiones de forma rápida.

**1. Crear el proyecto React y configurar Tailwind:**
Abre una **nueva pestaña** en tu terminal (para no cerrar Python), asegúrate de estar dentro de tu carpeta `kyc-project` y ejecuta:

```bash
# 1. Crear proyecto React
npm create vite@latest frontend -- --template react
cd frontend

# 2. Instalar dependencias base
npm install

# 3. Instalar y configurar Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**2. Configurar archivos de Tailwind:**
Abre el archivo `tailwind.config.js` recién creado y reemplaza su contenido por esto para que detecte tus archivos:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```
Luego, abre `src/index.css`, borra todo lo que tenga, y pega solo estas tres líneas:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**3. Crear la Interfaz Moderna:**
Abre `src/App.jsx`, borra todo y pega el código de tu nueva herramienta interna:

```jsx
import { useState } from 'react'

function App() {
  const [ine, setIne] = useState(null)
  const [selfie, setSelfie] = useState(null)
  const [resultados, setResultados] = useState(null)
  const [cargando, setCargando] = useState(false)

  const procesarImagenes = async (e) => {
    e.preventDefault()
    if (!ine || !selfie) return alert("Sube ambas imágenes por favor.")

    setCargando(true)
    setResultados(null)

    const formData = new FormData()
    formData.append("ine", ine)
    formData.append("selfie", selfie)

    try {
      const respuesta = await fetch("http://localhost:8000/api/verificar", {
        method: "POST",
        body: formData,
      })
      const datos = await respuesta.json()
      setResultados(datos)
    } catch (error) {
      setResultados({ error: "Error de conexión con el servidor Python." })
    }
    setCargando(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-md overflow-hidden">

        <div className="bg-blue-600 py-6 px-8">
          <h1 className="text-2xl font-bold text-white text-center">🛡️ Validador KYC Interno</h1>
          <p className="text-blue-100 text-center mt-2">Verificación Facial y Extracción de Pólizas</p>
        </div>

        <div className="p-8">
          <form onSubmit={procesarImagenes} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                <label className="block text-sm font-medium text-gray-700 mb-2">1. Registro (INE)</label>
                <input type="file" accept="image/*" onChange={(e) => setIne(e.target.files[0])} className="text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"/>
              </div>

              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                <label className="block text-sm font-medium text-gray-700 mb-2">2. Selfie + Póliza</label>
                <input type="file" accept="image/*" onChange={(e) => setSelfie(e.target.files[0])} className="text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"/>
              </div>
            </div>

            <button type="submit" disabled={cargando} className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${cargando ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'} transition-colors`}>
              {cargando ? 'Procesando imágenes con IA...' : 'Verificar Identidad'}
            </button>
          </form>

          {resultados && !resultados.error && (
            <div className="mt-8 bg-gray-50 border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 border-b pb-2 mb-4">Resultados de Validación</h3>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-white p-4 rounded shadow-sm border border-gray-100">
                  <p className="text-sm text-gray-500">¿Misma Persona?</p>
                  <p className={`text-xl font-bold ${resultados.misma_persona ? 'text-green-600' : 'text-red-600'}`}>
                    {resultados.misma_persona ? "SÍ ✅" : "NO ❌"}
                  </p>
                </div>
                <div className="bg-white p-4 rounded shadow-sm border border-gray-100">
                  <p className="text-sm text-gray-500">Nivel de Similitud</p>
                  <p className="text-xl font-bold text-gray-800">{resultados.similitud}%</p>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Texto Extraído (OCR):</p>
                <div className="bg-gray-800 text-green-400 p-4 rounded-md overflow-auto max-h-64 font-mono text-sm whitespace-pre-wrap">
                  {resultados.texto_extraido}
                </div>
              </div>
            </div>
          )}

          {resultados?.error && (
            <div className="mt-6 bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-sm text-red-700"><strong>Error:</strong> {resultados.error}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
```

**4. Arrancar el Frontend:**
En esa misma terminal, ejecuta:
```bash
npm run dev
```
Abre en tu navegador web la ruta `http://localhost:5173`. Tienes ahora una herramienta moderna, local, y lista para procesar tus validaciones.
