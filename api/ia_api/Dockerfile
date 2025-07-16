# 1. Utiliser l'image de base stable et légère
FROM python:3.11-slim

# 2. Installer uniquement les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# 3. Exposer uniquement le port de l'application
EXPOSE 8001

# Le reste de votre Dockerfile reste identique
# ------------------------------------------------
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copier les requirements
COPY api/ia_api/requirements.txt ./requirements-api.txt
COPY database/requirements.txt ./requirements-db.txt

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-api.txt && \
    pip install --no-cache-dir -r requirements-db.txt

# Télécharger et pré-packager le modèle IA
RUN python -c "\
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM;\
from peft import PeftModel;\
base = 'facebook/nllb-200-distilled-600M';\
adapter = 'Farid59/nllb-darija-lora-model';\
tokenizer = AutoTokenizer.from_pretrained(base);\
model = AutoModelForSeq2SeqLM.from_pretrained(base);\
peft = PeftModel.from_pretrained(model, adapter)\
"

# Copier le code de l'application
COPY api/ia_api/ ./api/ia_api/
COPY database/ ./database/

ENV PYTHONPATH=/app

# Utiliser la commande de démarrage directe pour Uvicorn
# Plus besoin de script entrypoint.sh
CMD ["uvicorn", "api.ia_api.main:app", "--host", "0.0.0.0", "--port", "8001"]