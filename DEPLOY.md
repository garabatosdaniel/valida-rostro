# Guia de Deploy en Railway

Guia paso a paso para desplegar el Validador KYC en [Railway](https://railway.app).

El proyecto se despliega como **dos servicios separados** dentro de un mismo proyecto en Railway:
- **Backend** (Python/FastAPI) - Procesa imagenes y llama a OpenRouter
- **Frontend** (React/Nginx) - Interfaz web que consume la API del backend

## Requisitos previos

- Cuenta en [Railway](https://railway.app) (se puede crear con GitHub)
- Repositorio en GitHub (ya lo tienes: `gmrdaniel/valida-rostro`)
- API key de [OpenRouter](https://openrouter.ai/keys)

## Paso 1: Crear el proyecto en Railway

1. Inicia sesion en [Railway](https://railway.app)
2. Clic en **"New Project"**
3. Selecciona **"Empty Project"**
4. Dale un nombre al proyecto (ej: `kyc-validador`)

## Paso 2: Desplegar el Backend

### 2.1 Crear el servicio

1. Dentro del proyecto, clic en **"New"** > **"GitHub Repo"**
2. Selecciona el repositorio `gmrdaniel/valida-rostro`
3. Railway detectara el repositorio y comenzara el build

### 2.2 Configurar el Root Directory

1. Ve a la pestana **Settings** del servicio
2. En **"Root Directory"** escribe: `backend`
3. Railway usara solo la carpeta `backend/` para este servicio

### 2.3 Configurar variables de entorno

Ve a la pestana **Variables** y agrega:

| Variable | Valor |
|---|---|
| `OPENROUTER_API_KEY` | `sk-or-v1-tu-api-key-aqui` |
| `ALLOWED_ORIGINS` | (lo configuras despues de tener la URL del frontend) |

> Railway inyecta `PORT` automaticamente, no necesitas agregarlo.

### 2.4 Verificar el deploy

1. Railway detectara el `Dockerfile` y construira la imagen automaticamente
2. El build tarda ~3-5 minutos (instala PyTorch para EasyOCR)
3. Una vez desplegado, ve a **Settings** > **Networking** > **"Generate Domain"**
4. Obtendras una URL como: `https://valida-rostro-backend-production.up.railway.app`
5. Verifica que funcione: abre `https://TU-URL/api/health` en el navegador

Deberias ver:
```json
{
  "status": "ok",
  "servicio": "KYC Validador de Identidad",
  "modelos": ["openai/gpt-4o-mini", "google/gemini-2.5-flash"],
  "verificacion": "doble",
  "procesamiento_local": ["deteccion_rostros", "ocr"]
}
```

## Paso 3: Desplegar el Frontend

### 3.1 Crear el servicio

1. En el mismo proyecto, clic en **"New"** > **"GitHub Repo"**
2. Selecciona el mismo repositorio `gmrdaniel/valida-rostro`

### 3.2 Configurar el Root Directory

1. Ve a **Settings** del nuevo servicio
2. En **"Root Directory"** escribe: `frontend`

### 3.3 Configurar la variable de build

Ve a la pestana **Variables** y agrega:

| Variable | Valor |
|---|---|
| `VITE_API_URL` | `https://TU-URL-DEL-BACKEND.up.railway.app` |

> Esta variable se usa en **tiempo de build** (Vite la reemplaza al compilar).
> Si la cambias despues, necesitas hacer un **Redeploy** para que tome efecto.

### 3.4 Verificar el deploy

1. Railway detectara el `Dockerfile` y construira la imagen
2. El build tarda ~1-2 minutos
3. Ve a **Settings** > **Networking** > **"Generate Domain"**
4. Obtendras una URL como: `https://valida-rostro-frontend-production.up.railway.app`
5. Abre esa URL en el navegador y prueba la aplicacion

## Paso 4: Conectar Backend con Frontend (CORS)

Ahora que tienes la URL del frontend, vuelve al servicio del **Backend**:

1. Ve a la pestana **Variables**
2. Actualiza `ALLOWED_ORIGINS` con la URL del frontend:
   ```
   ALLOWED_ORIGINS=https://valida-rostro-frontend-production.up.railway.app
   ```
3. Railway reiniciara el servicio automaticamente

## Paso 5: Verificar todo

1. Abre la URL del frontend en tu navegador
2. Sube una foto de identificacion y una selfie
3. Haz clic en "Verificar identidad"
4. Deberia mostrar el resultado de la comparacion y el texto extraido

## Troubleshooting

### El frontend no se conecta al backend
- Verifica que `VITE_API_URL` apunte a la URL correcta del backend
- Verifica que `ALLOWED_ORIGINS` en el backend incluya la URL del frontend
- Recuerda: `VITE_API_URL` se aplica en build time. Si la cambias, haz Redeploy del frontend

### El backend tarda mucho en arrancar
- La primera vez, EasyOCR descarga los modelos de idioma (~50-100MB)
- El `healthcheckTimeout` esta configurado en 300 segundos para cubrir esto
- Los siguientes arranques son mas rapidos (los modelos quedan en la imagen Docker)

### Error 502 Bad Gateway
- El backend no arranco correctamente. Revisa los logs en Railway
- Verifica que `OPENROUTER_API_KEY` este configurada correctamente

### El build del backend falla
- Puede ser falta de memoria. Railway Free Tier tiene limite de 8GB RAM
- Si falla por PyTorch, verifica que `requirements.txt` tenga las versiones correctas

## Arquitectura del deploy

```
Internet
   |
   v
[Frontend - Nginx]  <-- Railway Service 1 (puerto automatico)
   |                     URL: https://frontend.up.railway.app
   | fetch()
   v
[Backend - FastAPI]  <-- Railway Service 2 (puerto automatico)
   |                     URL: https://backend.up.railway.app
   |-- OpenCV DNN (local, deteccion de rostros)
   |-- EasyOCR (local, extraccion de texto)
   |-- OpenRouter API (remoto, solo recortes de rostro)
         |-- gpt-4o-mini
         |-- gemini-2.5-flash
```

## Costos estimados

| Recurso | Costo |
|---|---|
| Railway (Trial) | $5 USD gratis al registrarse |
| Railway (Hobby) | $5 USD/mes + uso |
| OpenRouter (10 validaciones/dia) | ~$0.01 USD/dia |

> Con el plan Trial de Railway puedes probar sin tarjeta de credito.
> El plan Hobby ($5/mes) incluye $5 de credito de uso, suficiente para este proyecto.
