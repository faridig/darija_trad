# Dockerfile: api/data_api/Dockerfile 

# Étape 1 : Image de base
FROM python:3.11-slim

# Étape 2 : Définir le répertoire de travail
WORKDIR /app

# Étape 3 : Installer les dépendances 
# On copie uniquement le fichier requirements.txt de la racine du projet
COPY requirements.txt ./

# On installe TOUTES les dépendances à partir de ce fichier unique.
# L'option --no-cache-dir est excellente pour garder l'image légère.
RUN pip install --no-cache-dir -r requirements.txt

# Étape 4 : Copier le code source de l'application
# On copie uniquement ce qui est nécessaire pour cette API.
COPY ./api/data_api/ ./api/data_api/
COPY ./database/ ./database/

# Étape 5 : Définir le chemin de recherche des modules Python
# Permet aux imports comme 'from database.core.db' de fonctionner.
ENV PYTHONPATH=/app

# Étape 6 : Commande pour lancer l'application
CMD ["uvicorn", "api.data_api.main:app", "--host", "0.0.0.0", "--port", "8000"]