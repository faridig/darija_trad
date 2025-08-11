# Dockerfile: api/ia_api/Dockerfile (Version pour Inférence via API Externe)

# On utilise une image Python de base, légère et suffisante.
FROM python:3.11-slim

# Définition des variables d'environnement (bonnes pratiques)
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# On copie le fichier des dépendances.
# Assurez-vous que ce fichier a été nettoyé (sans torch, transformers, etc.)
COPY requirements.txt ./

# On installe les dépendances, qui sont maintenant beaucoup plus légères.
# L'option --no-cache-dir permet de garder l'image petite.
RUN pip install --no-cache-dir -r requirements.txt

# On copie le code source de l'application nécessaire à son exécution.
COPY api/ia_api/ ./api/ia_api/
COPY database/ ./database/

# On expose le port sur lequel l'API va écouter.
EXPOSE 8001

# Commande pour lancer le serveur web Uvicorn.
# Cette commande ne change pas, elle est toujours correcte.
CMD ["uvicorn", "api.ia_api.main:app", "--host", "0.0.0.0", "--port", "8001"]