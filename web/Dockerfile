# Étape 1 : construire le front (fichiers statiques dans dist/).
FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# URL de l'API vide : le front appelle /api/v1/... sur la même adresse que la page,
# et Caddy transmet ces requêtes à l'API.
ENV VITE_API_BASE_URL=""
RUN npm run build

# Étape 2 : servir dist/ avec Caddy. L'image finale ne contient ni Node ni le code source.
FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
