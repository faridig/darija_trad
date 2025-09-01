# Fichier : api/ia_api/routers/monitoring.py
# Rôle : Ce module définit les endpoints essentiels pour la surveillance (monitoring)
# de l'API d'IA. Il expose des indicateurs de santé pour Kubernetes et des métriques
# détaillées pour Prometheus, tout en sécurisant l'accès à ces dernières.

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, Counter, Histogram, CONTENT_TYPE_LATEST
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging
from datetime import datetime
import os
import secrets
from dotenv import load_dotenv
from ..limiter import limiter


# Importe l'instance partagée du traducteur pour les tests de santé.
from .generation import translator
# Importe la logique de vérification de token, bien qu'elle ne soit pas utilisée
# directement sur ces routes (qui utilisent l'authentification Basic ou aucune).
from database.core.auth import verify_jwt_token

# ==============================================================================
# 1. INITIALISATION ET CONFIGURATION
# ==============================================================================

# Crée un routeur FastAPI dédié aux endpoints de monitoring.
# Le tag "Monitoring" regroupera ces routes dans la documentation Swagger UI.
router = APIRouter(tags=["Monitoring"])


# Charge les variables d'environnement depuis un fichier .env.
# C'est ici que sont récupérés les identifiants pour sécuriser l'endpoint /metrics.
load_dotenv()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Initialise le schéma de sécurité HTTP Basic. FastAPI l'utilisera pour
# générer la documentation et exiger une authentification `user:password`.
security = HTTPBasic()

# Configure un logger pour enregistrer les événements importants, comme les
# tentatives d'accès non autorisées, ce qui est crucial pour la sécurité.
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==============================================================================
# 2. DÉFINITION DES MÉTRIQUES PROMETHEUS
# ==============================================================================
# Chaque métrique est définie comme une variable globale pour être accessible
# depuis d'autres parties de l'application (notamment les middlewares).

# Métrique de type "Compteur" : une valeur qui ne fait qu'augmenter.
# Idéale pour compter le nombre total d'événements.
REQUEST_COUNT = Counter(
    'api_requests_total', # Nom de la métrique.
    'Total API requests', # Description pour Prometheus.
    ['method', 'endpoint'] # "Labels" pour segmenter les données (ex: GET /health).
)

# Métrique de type "Histogramme" : mesure la distribution des valeurs.
# Parfait pour suivre les temps de réponse (latence).
REQUEST_LATENCY = Histogram(
    'api_request_latency_seconds',
    'API request latency',
    ['method', 'endpoint']
)

# Histogramme spécifique au MLOps pour détecter la dérive des données (Data Drift).
# Il mesure la distribution de la longueur des textes soumis par les utilisateurs.
DATA_DRIFT_INPUT_LENGTH = Histogram(
    'data_drift_text_length',
    'Longueur du texte soumis au modèle (en nombre de mots)',
    # Les "buckets" (seaux) sont définis manuellement pour avoir une grande précision
    # sur les longueurs de texte les plus courantes et regrouper les valeurs extrêmes.
    buckets=(
        0, 3, 6, 9, 12, 15,  # <-- Haute résolution pour le cœur de la distribution (75% des données)
        20, 25, 30,          # <-- Résolution moyenne pour le début de la traîne
        40, 50,              # <-- Résolution plus faible pour les données plus rares
        75, 100, 150, 200     # <--- Larges seaux pour les outliers jusqu'à la limite max de l'API (200 mots)
    )
)

# Compteur pour suivre spécifiquement les erreurs serveur (codes 5xx).
# C'est un indicateur clé de la fiabilité de l'application.
HTTP_ERRORS_5XX_TOTAL = Counter(
    'api_http_errors_5xx_total',
    'Total number of internal server errors (5xx)',
    ['method', 'endpoint']
)

# ==============================================================================
# 3. ENDPOINTS DE MONITORING
# ==============================================================================

@router.get("/healthz", status_code=200)
@limiter.limit("30/minute")  # 30 requêtes par minute par IP
async def liveness_check(request: Request):
    """
    Sonde de vivacité ("Liveness Probe") pour Kubernetes.

    Cette route est volontairement très simple et rapide. Elle ne vérifie aucune
    dépendance externe (base de données, API distante). Son unique but est de
    répondre à la question : "Le processus du serveur web est-il en cours d'exécution ?".

    Si cette route ne répond pas, Kubernetes considérera que le conteneur est
    planté et le redémarrera.
    """
    return {"status": "ok"}

@router.get("/health")
@limiter.limit("10/minute")  # 10 requêtes par minute par IP
async def health_check(request: Request):
    """
    Sonde de préparation ("Readiness Probe") pour Kubernetes et vérification de santé.

    Cette route est plus complète que /healthz. Elle vérifie non seulement que le
    serveur est en vie, mais aussi qu'il est capable de remplir sa fonction principale,
    ce qui inclut la communication avec ses dépendances critiques (ici, le modèle d'IA distant).

    Si cette route échoue, Kubernetes considérera que le pod n'est pas prêt à
    recevoir du trafic et le retirera temporairement du service.
    """
    try:
        # On simule un appel réel au traducteur.
        test_text = "Test santé"
        _ = translator.traiter(test_text, src_lang="fra_Latn", tgt_lang="ary_Arab")
        
        # Si l'appel réussit, l'API est considérée comme saine.
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # Si l'appel au traducteur échoue (ex: l'API Hugging Face est en panne),
        # on capture l'erreur, on la logue, et on renvoie une erreur 500.
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Service unavailable")


@router.get("/metrics", include_in_schema=False)
@limiter.limit("5/minute")  # 5 requêtes par minute par IP
async def metrics(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    """
    Endpoint sécurisé qui expose les métriques au format textuel de Prometheus.

    - `include_in_schema=False`: Empêche cette route d'apparaître dans la
      documentation Swagger UI, car elle n'est pas destinée aux utilisateurs finaux.
    - `Depends(security)`: Indique à FastAPI que cette route nécessite une
      authentification HTTP Basic.

    Args:
        request (Request): La requête HTTP (requis pour le rate limiting)
        credentials (HTTPBasicCredentials): Injecté par FastAPI, contient le
                                            nom d'utilisateur et le mot de passe
                                            fournis par le client (Prometheus).
    """
    # Utilise `secrets.compare_digest` pour une comparaison en temps constant.
    # C'est une mesure de sécurité cruciale pour se prémunir contre les attaques
    # par analyse temporelle ("timing attacks").
    username_ok = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    password_ok = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)

    if not (username_ok and password_ok):
        logger.warning(f"Accès non autorisé à /metrics avec user={credentials.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    # `generate_latest()` collecte toutes les métriques enregistrées (Counter, Histogram, etc.)
    # et les formate en texte brut, prêtes à être lues ("scrapées") par Prometheus.
    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )