# api/ia_api/middlewares.py

"""
Ce module définit les middlewares FastAPI pour l'API d'IA.

Un middleware est une fonction qui traite chaque requête avant qu'elle n'atteigne
l'endpoint final, et chaque réponse avant qu'elle ne soit renvoyée au client.
C'est un mécanisme puissant pour injecter de la logique transversale comme
la sécurité, le logging ou le monitoring de manière centralisée.
"""

from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
from datetime import datetime
import json
import logging

# Importation des métriques Prometheus qui seront mises à jour par les middlewares.
from prometheus_client import Counter, Histogram
from .routers.monitoring import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    DATA_DRIFT_INPUT_LENGTH,
    HTTP_ERRORS_5XX_TOTAL
)

# Configuration d'un logger spécifique à ce module pour un suivi clair.
logger = logging.getLogger("middlewares")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ────────────────────────────────────────────────────────────────────────────────
# Middleware 1 : Ajout de headers de sécurité HTTP
# ────────────────────────────────────────────────────────────────────────────────
async def add_security_headers(request: Request, call_next):
    """
    Ajoute des en-têtes de sécurité HTTP aux réponses sortantes.

    Cette fonction renforce la sécurité de l'API en appliquant des politiques
    recommandées pour se prémunir contre des attaques courantes comme le
    clickjacking (X-Frame-Options) ou le Cross-Site Scripting (Content-Security-Policy).

    Args:
        request (Request): L'objet de la requête entrante.
        call_next (Callable): La fonction pour passer la requête au prochain
                              middleware ou à l'endpoint.

    Returns:
        Response: La réponse HTTP, modifiée avec les nouveaux en-têtes.
    """
    # Exécute d'abord l'endpoint pour obtenir la réponse de base.
    response: Response = await call_next(request)
    path = request.url.path

    # On applique une politique de sécurité plus souple pour les pages de documentation
    # (Swagger/ReDoc) car elles ont besoin de charger des scripts et styles externes.
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
        # Pour toutes les autres routes de l'API, on applique une politique très stricte.
        # Force les navigateurs à communiquer en HTTPS.
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Empêche l'API d'être intégrée dans une `iframe` (protection anti-clickjacking).
        response.headers["X-Frame-Options"] = "DENY"
        # Politique de sécurité du contenu restrictive.
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

    return response


# ────────────────────────────────────────────────────────────────────────────────
# Middleware 2 : Limitation stricte de la taille du corps de requête
# ────────────────────────────────────────────────────────────────────────────────
async def limit_body_size(request: Request, call_next):
    """
    Vérifie la taille du corps de la requête avant de la traiter.

    Ce middleware agit comme une protection contre les attaques par déni de service (DoS)
    en rejetant immédiatement les requêtes dont le payload est trop volumineux,
    avant même que l'application ne commence à le traiter.

    Args:
        request (Request): L'objet de la requête entrante.
        call_next (Callable): La fonction pour passer au middleware suivant.

    Returns:
        Response: Une réponse d'erreur 413 si le payload est trop grand, sinon
                  la réponse de l'endpoint.
    """
    max_bytes = 10 * 1024  # 10KB
    
    content_length = request.headers.get("content-length")
    
    if content_length:
        try:
            # Convertir en entier et vérifier la taille
            if int(content_length) > max_bytes:
                return Response(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content="Payload trop volumineux. Maximum 10KB autorisé."
                )
        except ValueError:
            # Si content-length n'est pas un nombre valide, on laisse passer
            # La validation se fera ailleurs (par exemple dans les modèles Pydantic)
            pass
    
    # Si pas de content-length ou content-length invalide, on laisse passer
    response = await call_next(request)
    return response


# ────────────────────────────────────────────────────────────────────────────────
# Middleware 3 : Monitoring Prometheus & logging
# ────────────────────────────────────────────────────────────────────────────────
async def monitoring_middleware(request: Request, call_next):
    """
    Middleware central pour le monitoring et le logging.

    Il intercepte chaque requête pour :
    1.  Mesurer sa durée d'exécution (latence).
    2.  Incrémenter les compteurs de requêtes Prometheus.
    3.  Analyser le corps de la requête `/generer` pour le suivi du data drift.
    4.  Capturer les réponses d'erreur serveur (5xx) pour le suivi de la fiabilité.
    5.  Logger un résumé de chaque requête (méthode, chemin, statut, durée).

    Args:
        request (Request): L'objet de la requête entrante.
        call_next (Callable): La fonction pour passer au middleware suivant.

    Returns:
        Response: La réponse finale de l'endpoint.
    """
    start_time = datetime.now()
    method = request.method
    endpoint = request.url.path

    # Incrémente le compteur total de requêtes pour cet endpoint.
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    # Logique spécifique au data drift : on ne l'exécute que pour la route de traduction.
    if method == "POST" and endpoint == "/generer":
        try:
            # `await request.body()` "consomme" le corps de la requête.
            # C'est une opération délicate qui ne peut être faite qu'une fois.
            body = await request.body()
            if body:
                parsed = json.loads(body)
                texte = parsed.get("texte", "")
                longueur = len(texte.strip().split())
                # Enregistre la longueur du texte dans l'histogramme Prometheus.
                DATA_DRIFT_INPUT_LENGTH.observe(longueur)
        except Exception as e:
            # Si le parsing échoue, on log un avertissement mais on ne bloque pas la requête.
            logger.warning(f"[Monitoring] Erreur parsing drift : {e}")

    try:
        # On passe la requête à l'endpoint et on attend la réponse.
        response = await call_next(request)

        # ➤ Cas 1 : Erreur gérée.
        # Si la réponse a un code de statut 500 ou plus (erreur serveur),
        # cela signifie que l'endpoint a géré l'erreur mais a échoué.
        if response.status_code >= 500:
            # On incrémente le compteur d'erreurs 5xx.
            HTTP_ERRORS_5XX_TOTAL.labels(method=method, endpoint=endpoint).inc()

    except Exception as e:
        # ➤ Cas 2 : Erreur non gérée.
        # Si une exception s'échappe de `call_next`, cela signifie qu'une erreur
        # inattendue s'est produite. C'est aussi une erreur 5xx.
        HTTP_ERRORS_5XX_TOTAL.labels(method=method, endpoint=endpoint).inc()

        # On log l'erreur pour le débogage.
        logger.error(f"[Monitoring] Échec de la requête {method} {endpoint} - {e}")
        # On propage l'exception pour que FastAPI puisse la gérer et renvoyer une réponse 500 standard.
        raise

    # Calcule la durée totale de la requête en secondes.
    duration = (datetime.now() - start_time).total_seconds()
    # Enregistre cette durée dans l'histogramme de latence de Prometheus.
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    # Loggue un résumé formaté de la requête, utile pour le débogage en temps réel.
    logger.info(f"{method} {endpoint} - {response.status_code} - {duration:.3f}s")

    return response