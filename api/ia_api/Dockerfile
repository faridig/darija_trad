# Dockerfile: api/ia_api/Dockerfile (Version optimisée multi-étapes)

# ==============================================================================
# ÉTAPE 1: "BUILDER" - Installation des dépendances
# Cette étape installe tout, y compris les outils de compilation.
# ==============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Installation des dépendances système UNIQUEMENT dans cette étape
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python depuis le fichier unique
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# ==============================================================================
# ÉTAPE 2: "FINAL" - Création de l'image de production légère
# Cette étape repart d'une base propre et ne copie que le strict nécessaire.
# ==============================================================================
FROM python:3.11-slim

# Définition des variables d'environnement
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Copie des paquets installés depuis l'étape "builder"
# C'est la magie du multi-stage : on récupère les bibliothèques sans les outils de build.
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Copie du code de l'application
COPY api/ia_api/ ./api/ia_api/
COPY database/ ./database/

# Téléchargement et mise en cache du modèle IA
# Cette étape est longue, mais elle est mise après la copie du code
# pour que le cache Docker soit utilisé efficacement.
# Si seul le code change, cette étape ne sera pas ré-exécutée.
RUN python -c "\
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM;\
from peft import PeftModel;\
print('Téléchargement du tokenizer et du modèle de base...');\
base = 'facebook/nllb-200-distilled-600M';\
tokenizer = AutoTokenizer.from_pretrained(base);\
model = AutoModelForSeq2SeqLM.from_pretrained(base);\
print('Téléchargement et application de l"adaptateur LoRA...');\
adapter = 'Farid59/nllb-darija-lora-model';\
peft = PeftModel.from_pretrained(model, adapter);\
print('Mise en cache terminée.')\
"

# Exposition du port de l'application
EXPOSE 8001

# Commande pour lancer l'application
CMD ["uvicorn", "api.ia_api.main:app", "--host", "0.0.0.0", "--port", "8001"]