# api/ia_api/routers/monitoring.py

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, Counter, Histogram, CONTENT_TYPE_LATEST
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging
from datetime import datetime
import json
import os
import secrets
from dotenv import load_dotenv

from ..model import LLMTranslator                # <-- import modifié
from database.core.db import get_db
from database.core.auth import verify_jwt_token

# Init router
router = APIRouter(tags=["Monitoring"])

# Charger .env
load_dotenv()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Basic auth object
security = HTTPBasic()

# Logs
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Métriques Prometheus
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint']
)

REQUEST_LATENCY = Histogram(
    'api_request_latency_seconds',
    'API request latency',
    ['method', 'endpoint']
)

DATA_DRIFT_INPUT_LENGTH = Histogram(
    'data_drift_text_length',
    'Longueur du texte soumis au modèle',
    buckets=(0, 10, 20, 40, 60, 80, 100, 150, 200)
)

# Modèle pour health check
modele = LLMTranslator("Farid59/nllb-darija-lora-model")   # <-- classe renommée

@router.get("/health")
async def health_check(
    token: dict = Depends(verify_jwt_token),
    db=Depends(get_db)
):
    """Endpoint de vérification de santé"""
    try:
        test_text = "Test santé"
        # on suppose fra_Latn->ary_Arab par défaut ; on peut préciser si besoin
        _ = modele.traiter(test_text, src_lang="fra_Latn", tgt_lang="ary_Arab")
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Service unavailable")


@router.get("/metrics", include_in_schema=False)
async def metrics(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Endpoint sécurisé pour Prometheus.
    Authentification HTTP Basic (utilise ADMIN_USERNAME / ADMIN_PASSWORD)
    """
    username_ok = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    password_ok = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)

    if not (username_ok and password_ok):
        logger.warning(f"Accès non autorisé à /metrics avec user={credentials.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


async def monitoring_middleware(request: Request, call_next):
    """Middleware pour le tracking des requêtes"""
    start_time = datetime.now()
    endpoint = request.url.path
    method = request.method

    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    if method == "POST" and endpoint == "/generer":
        try:
            body = await request.body()
            if body:
                parsed_body = json.loads(body)
                texte = parsed_body.get("texte", "")
                longueur = len(texte.strip().split())
                DATA_DRIFT_INPUT_LENGTH.observe(longueur)
        except Exception as e:
            logger.warning(f"Erreur parsing drift : {e}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {method} {endpoint} - {str(e)}")
        raise

    processing_time = (datetime.now() - start_time).total_seconds()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(processing_time)

    logger.info(f"{method} {endpoint} - {response.status_code} - {processing_time:.3f}s")
    return response
