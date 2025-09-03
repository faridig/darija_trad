# frontend/Dockerfile

# ===================================================================
# Étape 1: "Builder" - Construction de l'application JavaScript
# ===================================================================
# On part d'une image Node.js pour compiler notre code.
FROM node:18-alpine as builder

# On définit le répertoire de travail dans l'image.
WORKDIR /app

# On copie les fichiers de définition des dépendances.
COPY package*.json ./

# On installe les dépendances. 'npm ci' est plus rapide et plus sûr pour la CI.
RUN npm ci

# On copie le reste du code source.
COPY . .

# On lance le build de production. Cela crée les fichiers statiques (html, js, css)
# dans le dossier /app/dist.
RUN npm run build


# ===================================================================
# Étape 2: "Production" - Création de l'image finale légère
# ===================================================================
# On part d'une image Nginx très légère.
FROM nginx:stable-alpine

# On copie les fichiers construits à l'étape précédente dans le dossier
# où Nginx sert les fichiers.
COPY --from=builder /app/dist /usr/share/nginx/html


# ===================================================================
# On copie notre script "messager" (entrypoint.sh) dans l'image.
COPY entrypoint.sh /entrypoint.sh

# On s'assure qu'il a les permissions pour être exécuté.
RUN chmod +x /entrypoint.sh

# On définit ce script comme étant la SEULE chose à lancer au démarrage
# du conteneur. C'est le changement le plus important.
ENTRYPOINT ["/entrypoint.sh"]
# ===================================================================


# On expose le port 80, sur lequel Nginx écoute.
EXPOSE 80

# On supprime l'ancienne commande CMD car c'est maintenant notre
# entrypoint.sh qui se charge de lancer Nginx.
# CMD ["nginx", "-g", "daemon off;"] # ANCIENNE LIGNE (maintenant inutile)