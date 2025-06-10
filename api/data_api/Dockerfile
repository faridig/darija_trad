FROM python:3.11-slim

WORKDIR /app

COPY api/data_api/requirements.txt api/data_api/requirements.txt
COPY database/requirements.txt database/requirements.txt

RUN pip install --no-cache-dir -r api/data_api/requirements.txt && \
    pip install --no-cache-dir -r database/requirements.txt

# Copier le code
COPY api/data_api/ ./api/data_api/
COPY database/ ./database/

# Copier le fichier .env (s'il est à la racine)
COPY .env .env

ENV PYTHONPATH=/app

CMD ["uvicorn", "api.data_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
