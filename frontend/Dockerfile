# frontend/Dockerfile

# ---- Etapa 1: Build ----
# Usa Node.js 18 Alpine como base para construir
FROM node:18-alpine AS build

WORKDIR /app

# Copia package.json y package-lock.json (si existe)
COPY package*.json ./

# Instala dependencias de Node.js
RUN npm install

# Copia el resto del código fuente de la app
COPY . .

# Ejecuta el script de build definido en package.json (tsc && vite build)
RUN npm run build

# Comando útil para depurar: lista el contenido de /app/dist para ver si se creó
RUN ls -la /app/dist

# ---- Etapa 2: Serve ----
# Usa Nginx Alpine como base para servir los archivos estáticos
FROM nginx:stable-alpine

# Copia los archivos construidos en la etapa anterior al directorio web de Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copia tu archivo de configuración personalizado de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expone el puerto 80 (puerto estándar HTTP)
EXPOSE 80

# Comando para iniciar Nginx en primer plano cuando el contenedor arranque
CMD ["nginx", "-g", "daemon off;"]