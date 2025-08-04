# frontend/Dockerfile

# ===================================================================
# Étape 1 : Le "Builder"
# Utilise une image Node.js pour installer les dépendances et construire l'application.
# ===================================================================
FROM node:18-alpine AS builder

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de définition des dépendances
# On copie package.json et package-lock.json en premier pour profiter du cache Docker.
# Si ces fichiers ne changent pas, Docker n'exécutera pas 'npm install' à chaque build.
COPY package.json package-lock.json ./

# Installer les dépendances
RUN npm install

# Copier tout le reste du code source de l'application
COPY . .

# Construire l'application pour la production
RUN npm run build

# À la fin de cette étape, notre application buildée se trouve dans /app/dist

# ===================================================================
# Étape 2 : La "Production"
# Utilise une image Nginx très légère pour servir les fichiers statiques.
# ===================================================================
FROM nginx:1.25-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# AJOUT: Copier notre configuration Nginx personnalisée
# Cela va écraser la configuration par défaut de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exposer le port 80
EXPOSE 80