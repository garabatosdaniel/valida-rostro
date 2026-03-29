# =============================================================================
# Dockerfile - Frontend React (Build + Nginx)
# =============================================================================
# Usa un build multi-stage:
#   1. Stage "build": Compila React con Vite (genera archivos estaticos)
#   2. Stage "production": Sirve los archivos con Nginx (servidor web ligero)
# =============================================================================

# --- Stage 1: Build ---
# Usamos Node 20 para compilar el proyecto React
FROM node:20-alpine AS build

WORKDIR /app

# Copiar archivos de dependencias primero (cache de Docker)
COPY package*.json ./

# Instalar dependencias
RUN npm ci

# Copiar el resto del codigo fuente
COPY . .

# Construir la app para produccion
# La variable VITE_API_URL se debe pasar como build arg
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Stage 2: Produccion ---
# Nginx sirve los archivos estaticos generados por Vite
FROM nginx:alpine

# Copiar los archivos compilados al directorio que Nginx sirve
COPY --from=build /app/dist /usr/share/nginx/html

# Configuracion de Nginx para SPA (Single Page Application)
# Redirige todas las rutas a index.html para que React Router funcione
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Railway inyecta PORT; Nginx escucha en ese puerto
EXPOSE 80

# Arrancar Nginx en primer plano (requerido por Docker)
CMD ["sh", "-c", "sed -i 's/listen 80/listen ${PORT:-80}/' /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
