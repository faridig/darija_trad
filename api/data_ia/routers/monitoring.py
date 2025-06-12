from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, Counter, Histogram, CONTENT_TYPE_LATEST
import logging
from datetime import datetime
from ..model import LLMDarija
from database.core.db import get_db
from database.core.auth import verify_jwt_token
from fastapi import Depends




router = APIRouter(tags=["Monitoring"])

# Configuration des logs
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

# Instance de modèle pour le health check
modele = LLMDarija("llm/nllb-darija-lora-model")

@router.get("/health")
async def health_check(
    token: dict = Depends(verify_jwt_token),
    db=Depends(get_db)
):
    """Endpoint de vérification de santé"""
    try:
        test_text = "Test santé"
        _ = modele.traiter(test_text)
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Service unavailable")


@router.get("/metrics")
async def metrics():
    """Endpoint des métriques Prometheus"""
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
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {method} {endpoint} - {str(e)}")
        raise
    
    processing_time = (datetime.now() - start_time).total_seconds()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(processing_time)
    
    logger.info(f"{method} {endpoint} - {response.status_code} - {processing_time:.3f}s")
    return response