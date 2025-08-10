# api/ia_api/routers/monitoring.py  -----

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, Counter, Histogram, CONTENT_TYPE_LATEST
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging
from datetime import datetime
import os
import secrets
from dotenv import load_dotenv

from .generation import translator
from database.core.auth import verify_jwt_token

# Init routerr
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
    'Longueur du texte soumis au modèle (en nombre de mots)',
    buckets=(
        0, 3, 6, 9, 12, 15,  # <-- Haute résolution pour le cœur de la distribution (75% des données)
        20, 25, 30,          # <-- Résolution moyenne pour le début de la traîne
        40, 50,              # <-- Résolution plus faible pour les données plus rares
        75, 100, 150, 200     # <--- Larges seaux pour les outliers jusqu'à la limite max de l'API (200 mots)
    )
)

HTTP_ERRORS_5XX_TOTAL = Counter(
    'api_http_errors_5xx_total',
    'Total number of internal server errors (5xx)',
    ['method', 'endpoint']
)



@router.get("/health")
async def health_check():
    """Endpoint de vérification de santé"""
    try:
        test_text = "Test santé"
        
        _ = translator.traiter(test_text, src_lang="fra_Latn", tgt_lang="ary_Arab")
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