FROM python:3.11-slim

# Eviter les surprises de timezone et langue
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installer pip et dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Créer et utiliser le dossier de travail
WORKDIR /app

# Copier les fichiers requirements AVANT le code pour optimiser le cache Docker
COPY api/ia_api/requirements.txt ./requirements-api.txt
COPY database/requirements.txt ./requirements-db.txt

# Installer les dépendances en une seule couche
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-api.txt && \
    pip install --no-cache-dir -r requirements-db.txt

# Téléchargement des modèles à build-time pour éviter les erreurs réseau au runtime
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

# Définir le PYTHONPATH
ENV PYTHONPATH=/app

# Commande de démarrage
CMD ["uvicorn", "api.ia_api.main:app", "--host", "0.0.0.0", "--port", "8001"]
