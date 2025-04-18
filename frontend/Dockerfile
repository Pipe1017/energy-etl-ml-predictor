# frontend/Dockerfile

# ---- Etapa 1: Build ----
# Usa una imagen de Node para construir la aplicación React
FROM node:18-alpine AS build

# Establece el directorio de trabajo
WORKDIR /app

# Copia package.json y package-lock.json (o yarn.lock)
COPY package*.json ./
# COPY yarn.lock ./ # Descomenta si usas yarn

# Instala las dependencias
RUN npm install
# RUN yarn install # Descomenta si usas yarn

# Copia el resto del código fuente del frontend
COPY . .

# Construye la aplicación para producción
RUN npm run build
# RUN yarn build # Descomenta si usas yarn

# ---- Etapa 2: Serve ----
# Usa una imagen ligera de Nginx para servir los archivos estáticos
FROM nginx:stable-alpine

# Copia los archivos construidos desde la etapa 'build' al directorio web raíz de Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copia una configuración personalizada de Nginx (la crearemos a continuación)
# Esta configuración es CLAVE para manejar el enrutamiento de React y el proxy a la API
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expone el puerto 80 (puerto estándar HTTP de Nginx)
EXPOSE 80

# Nginx se iniciará automáticamente por el comando por defecto de la imagen base