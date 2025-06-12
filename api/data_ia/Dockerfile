FROM python:3.11-slim

WORKDIR /app

COPY api/data_ia/requirements.txt api/data_ia/requirements.txt
COPY database/requirements.txt database/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r api/data_ia/requirements.txt && \
    pip install --no-cache-dir -r database/requirements.txt

# Copier le code
COPY api/data_ia/ ./api/data_ia/
COPY database/ ./database/

# Copier le fichier .env (s'il est à la racine)
# COPY .env .env

ENV PYTHONPATH=/app

CMD ["uvicorn", "api.data_ia.main:app", "--host", "0.0.0.0", "--port", "8001"]
