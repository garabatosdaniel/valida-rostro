# Validador KYC - Verificacion de Identidad

Sistema de verificacion de identidad (Know Your Customer) que compara rostros entre una identificacion oficial y una selfie, y extrae texto de documentos.

Usa un **enfoque hibrido de privacidad**: la deteccion de rostros y el OCR se ejecutan localmente, y solo los recortes de rostro (sin datos personales) se envian a Gemini para la comparacion facial.

## Privacidad de datos

| Proceso | Donde se ejecuta | Datos que salen de tu computadora |
|---|---|---|
| Deteccion y recorte de rostros | LOCAL (OpenCV DNN) | Ninguno |
| Extraccion de texto (OCR) | LOCAL (EasyOCR) | Ninguno |
| Comparacion facial | REMOTO (OpenRouter/Gemini) | Solo recortes de rostro (~100-200KB) |

Los datos personales de la identificacion (nombre, CURP, direccion, clave de elector) **nunca salen de tu computadora**.

## Stack Tecnologico

| Componente | Tecnologia |
|---|---|
| Backend (API) | Python, FastAPI |
| Deteccion de rostros | OpenCV DNN (local, SSD ResNet-10) |
| Extraccion de texto | EasyOCR (local, PyTorch) |
| Comparacion facial | OpenRouter doble verificacion: gpt-4o-mini + gemini-2.5-flash (remoto, solo rostros) |
| Frontend (UI) | React, Vite, Tailwind CSS |
| Deploy | Docker, Railway |

## Estructura del Proyecto

```
valida-rostro/
├── backend/
│   ├── main.py              # API principal (FastAPI)
│   ├── requirements.txt     # Dependencias Python
│   ├── models/              # Modelos de deteccion facial (OpenCV DNN)
│   │   ├── deploy.prototxt
│   │   └── res10_300x300_ssd_iter_140000.caffemodel
│   ├── Dockerfile           # Imagen Docker para Railway
│   ├── railway.toml         # Config de deploy Railway
│   └── .env.example         # Variables de entorno ejemplo
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Componente principal React
│   │   ├── main.jsx         # Punto de entrada
│   │   └── index.css        # Tailwind CSS
│   ├── Dockerfile           # Imagen Docker para Railway
│   ├── nginx.conf           # Config de Nginx para SPA
│   ├── railway.toml         # Config de deploy Railway
│   └── .env.example         # Variables de entorno ejemplo
├── .gitignore
└── README.md
```

## Instalacion Local

### Requisitos

- Python 3.10+
- Node.js 18+
- Git
- Una API key de [OpenRouter](https://openrouter.ai/keys)

### 1. Clonar el repositorio

```bash
git clone https://github.com/gmrdaniel/valida-rostro.git
cd valida-rostro
```

### 2. Backend

```bash
# Entrar a la carpeta del backend
cd backend

# Crear y activar entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar variables de entorno y configurar tu API key
cp .env.example .env
```

Edita el archivo `.env` y agrega tu API key de OpenRouter:

```
OPENROUTER_API_KEY=sk-or-v1-tu-api-key-aqui
```

Arranca el servidor:

```bash
# Arrancar el servidor (puerto 8000)
python main.py
```

> La primera vez que se ejecuta, EasyOCR descarga los modelos de idioma (~50-100MB). Esto solo ocurre una vez.

**Variables de entorno del backend** (archivo `.env`):

| Variable | Descripcion | Valor en local | Valor en produccion |
|---|---|---|---|
| `OPENROUTER_API_KEY` | API key de OpenRouter (obligatoria) | Tu key de openrouter.ai/keys | Misma key o variable en Railway |
| _(modelos)_ | Doble verificacion: gpt-4o-mini + gemini-2.5-flash | Configurados en main.py | Igual |
| `ALLOWED_ORIGINS` | Origenes permitidos para CORS | `http://localhost:5173` (default) | URL de tu frontend en Railway |
| `PORT` | Puerto del servidor | `8000` (default) | Railway lo inyecta automaticamente |

### 3. Frontend

Abre una **nueva terminal** (deja el backend corriendo):

```bash
# Entrar a la carpeta del frontend
cd frontend

# Instalar dependencias
npm install

# Arrancar el servidor de desarrollo (puerto 5173)
npm run dev
```

**Variable de entorno del frontend** (opcional):

| Variable | Descripcion | Valor en local | Valor en produccion |
|---|---|---|---|
| `VITE_API_URL` | URL del backend | No necesaria (usa `http://localhost:8000` por defecto) | URL de tu backend en Railway |

En local no necesitas crear `.env` para el frontend. Solo es necesario en produccion: crea un archivo `.env` en la carpeta `frontend/` con `VITE_API_URL=https://tu-backend.railway.app` o configuralo como variable de entorno en Railway.

### 4. Usar la aplicacion

Abre tu navegador en `http://localhost:5173`:

1. Sube la foto de una identificacion (INE, pasaporte, etc.)
2. Sube una selfie de la persona
3. Haz clic en "Verificar Identidad"
4. El sistema mostrara si es la misma persona, el porcentaje de similitud y el texto extraido

## Como funciona

1. El usuario sube una foto de su INE y una selfie
2. **LOCAL**: OpenCV DNN detecta los rostros en ambas imagenes y recorta el mas grande (ignora la foto fantasma de la INE)
3. **LOCAL**: EasyOCR extrae el texto de la INE (nombre, CURP, direccion, etc.)
4. **REMOTO**: Solo los recortes de rostro se envian a Gemini via OpenRouter para determinar si es la misma persona
5. El frontend muestra el resultado: si coinciden, porcentaje de similitud y texto extraido

## Deploy en Railway

### 1. Crear proyecto en Railway

- Crea una cuenta en [Railway](https://railway.app)
- Crea un nuevo proyecto

### 2. Desplegar el Backend

- En Railway, clic en "New Service" > "GitHub Repo"
- Selecciona este repositorio
- En Settings > Root Directory: `backend`
- Agrega las variables de entorno:
  - `OPENROUTER_API_KEY` = tu API key de OpenRouter
  - `ALLOWED_ORIGINS` = `https://tu-frontend.railway.app`
- Railway detectara el Dockerfile y desplegara automaticamente

### 3. Desplegar el Frontend

- Crea otro servicio en el mismo proyecto
- Selecciona el mismo repositorio
- En Settings > Root Directory: `frontend`
- Agrega la variable de build:
  - `VITE_API_URL` = `https://tu-backend.railway.app`
- Railway construira y desplegara automaticamente

## API Endpoints

| Metodo | Ruta | Descripcion |
|---|---|---|
| POST | `/api/verificar` | Recibe dos imagenes (ine, selfie) y retorna verificacion facial + OCR |
| GET | `/api/health` | Health check del servicio |

### Ejemplo de respuesta `/api/verificar`

```json
{
  "misma_persona": true,
  "similitud": 95,
  "texto_extraido": "INSTITUTO NACIONAL ELECTORAL\nNOMBRE: JUAN PEREZ\nCURP: XXXX000000XXXXXX00"
}
```

## Doble verificacion

El backend consulta **dos modelos en paralelo** y solo aprueba si ambos coinciden. Esto elimina los falsos positivos que cada modelo tiene individualmente:

| Estrategia | Precision | Notas |
|---|---|---|
| **Doble: gpt-4o-mini + gemini-2.5-flash** | **100% (6/6)** | Ambos deben aprobar |
| Solo gpt-4o-mini | 83% (5/6) | Falla en un impostor |
| Solo gemini-2.5-flash | 83% (5/6) | Falla en otro impostor |

Benchmark con 6 pares de prueba (3 misma persona + 3 personas diferentes).
