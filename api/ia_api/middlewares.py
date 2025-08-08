# api/ia_api/middlewares.py

from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
from datetime import datetime
import json
import logging

from prometheus_client import Counter, Histogram
from .routers.monitoring import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    DATA_DRIFT_INPUT_LENGTH,
    HTTP_ERRORS_5XX_TOTAL  # L'import est déjà présent, c'est parfait
)

# Configuration du logger
logger = logging.getLogger("middlewares")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ────────────────────────────────────────────────────────────────────────────────
# Middleware 1 : Ajout de headers de sécurité HTTP
# ────────────────────────────────────────────────────────────────────────────────
async def add_security_headers(request: Request, call_next):
    # ... (Ce middleware ne change pas)
    response: Response = await call_next(request)
    path = request.url.path

    if any(path.startswith(p) for p in (
        "/docs", "/docs/oauth2-redirect", "/openapi", "/redoc",
        "/favicon.ico", "/static"
    )):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://cdn.jsdelivr.net; "
            "connect-src 'self' https://cdn.jsdelivr.net; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "frame-ancestors 'none';"
        )
    else:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

    return response


# ────────────────────────────────────────────────────────────────────────────────
# Middleware 2 : Limitation stricte de la taille du corps de requête
# ────────────────────────────────────────────────────────────────────────────────
async def limit_body_size(request: Request, call_next):
    # ... (Ce middleware ne change pas)
    max_bytes = 10 * 1024
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_bytes:
        return FastAPIResponse("Payload trop volumineux", status_code=413)
    return await call_next(request)


# ────────────────────────────────────────────────────────────────────────────────
# Middleware 3 : Monitoring Prometheus & logging (durée, drift, etc.) - MIS À JOUR
# ────────────────────────────────────────────────────────────────────────────────
async def monitoring_middleware(request: Request, call_next):
    start_time = datetime.now()
    method = request.method
    endpoint = request.url.path

    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    if method == "POST" and endpoint == "/generer":
        try:
            body = await request.body()
            if body:
                parsed = json.loads(body)
                texte = parsed.get("texte", "")
                longueur = len(texte.strip().split())
                DATA_DRIFT_INPUT_LENGTH.observe(longueur)
        except Exception as e:
            logger.warning(f"[Monitoring] Erreur parsing drift : {e}")

    try:
        response = await call_next(request)
  
        # ➤ On vérifie le code de statut de la réponse. Si c'est une erreur serveur...
        if response.status_code >= 500:
            # ... on incrémente le compteur d'erreurs 5xx.
            HTTP_ERRORS_5XX_TOTAL.labels(method=method, endpoint=endpoint).inc()
     
    except Exception as e:
    
        # ➤ Si une exception non gérée se produit, c'est une erreur 500.
        # On l'enregistre aussi avant de propager l'exception.
        HTTP_ERRORS_5XX_TOTAL.labels(method=method, endpoint=endpoint).inc()
  
        logger.error(f"[Monitoring] Échec de la requête {method} {endpoint} - {e}")
        raise # On propage l'exception pour que FastAPI génère la réponse 500

    duration = (datetime.now() - start_time).total_seconds()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    logger.info(f"{method} {endpoint} - {response.status_code} - {duration:.3f}s")

    return response