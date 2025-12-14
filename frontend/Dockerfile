# Frontend Dockerfile - Version Sécurisée (Corrigée)

# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app

# Copier package files
COPY package*.json ./

# Installer TOUTES les dépendances (y compris dev pour le build)
RUN npm ci

# Copier le code source
COPY . .

# Build argument pour l'API URL
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build de l'application
RUN npm run build

# Stage 2 Production avec Nginx
FROM nginx:1.25-alpine

# Créer un utilisateur non-root
RUN addgroup -g 101 -S nginx && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx 2>/dev/null || true

# Copier la configuration Nginx personnalisée
COPY nginx.conf /etc/nginx/nginx.conf

# Copier les fichiers buildés
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Permissions pour nginx
RUN chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Passer à l'utilisateur non-root
USER nginx

# Exposer le port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# Démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]