# Fichier: api/ia_api/main.py
# Rôle: Point d'entrée principal de l'API d'Inférence (IA).
#
# Ce script initialise l'application FastAPI et configure tous les aspects
# globaux qui s'appliquent à l'ensemble des requêtes :
#   - Middlewares (CORS, Rate Limiting, Monitoring, etc.).
#   - Gestionnaires d'exceptions personnalisés pour des réponses d'erreur uniformes.
#   - Intégration des "routeurs" qui contiennent la logique des endpoints spécifiques.

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Test de déclenchement du pipeline CI/CD

# Importation des modules contenant les groupes de routes (endpoints).
# Cette approche modulaire permet de garder le code organisé et maintenable.
from api.ia_api.routers import generation, monitoring

# Importation des fonctions middleware personnalisées définies dans un fichier séparé.
from api.ia_api.middlewares import (
    add_security_headers,
    limit_body_size,
    monitoring_middleware
)

# ==============================================================================
# --- ÉTAPE 1 : INITIALISATION DE L'APPLICATION FASTAPI ---------
# ==============================================================================
# C'est ici que l'objet principal de l'application est créé.
# Le titre, la version et la description apparaîtront dans la documentation
# interactive (Swagger UI), la rendant plus claire pour les utilisateurs.
app = FastAPI(
    title="IA Translation API",
    version="1.0",
    description="""
🤖 **API d'Inférence pour la Traduction**

Cette API utilise un modèle d'IA pour traduire du texte. Elle est sécurisée par JWT.

**Comment l'utiliser :**

1.  Obtenez un token d'accès en faisant un `POST /login` sur l'**API de Données** (`data-api`).
2.  Copiez le `access_token` retourné.
3.  Cliquez sur le bouton 🔐 "Authorize" en haut à droite de cette page.
4.  Dans la fenêtre qui apparaît, collez votre token sous la forme `Bearer <votre_token>`.

⚠️ Toutes les routes de cette API (comme `/generer`) nécessitent un token valide.
""",
    # Paramètres pour améliorer l'ergonomie de la documentation Swagger.
    swagger_ui_parameters={
        "jsonEditor": False,
        "defaultModelRendering": "model",
    },
)

# ==============================================================================
# --- ÉTAPE 2 : CONFIGURATION DES MIDDLEWARES --------
# Les middlewares sont des fonctions qui traitent chaque requête avant qu'elle
# n'atteigne l'endpoint, et chaque réponse avant son envoi.
# L'ordre d'enregistrement est important.
# ==============================================================================

# Middleware n°1 : CORS (Cross-Origin Resource Sharing)
# Essentiel pour la sécurité des navigateurs. Il autorise explicitement
# notre application frontend (servie sur une autre origine) à envoyer des
# requêtes à cette API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Pour le développement local du frontend
        "http://4.178.216.44"       # L'IP de votre frontend déployé
    ],
    allow_credentials=True, # Autorise l'envoi de cookies ou de headers d'authentification.
    allow_methods=["*"],  # Autorise toutes les méthodes HTTP (GET, POST, etc.).
    allow_headers=["*"]   # Autorise tous les en-têtes (comme Authorization).
)

# Middleware n°2 : Headers de sécurité
app.middleware("http")(add_security_headers)

# Middleware n°3 (personnalisé) : Limitation de la taille du corps de la requête.
# Une mesure de sécurité simple pour prévenir les attaques par déni de service
# où un attaquant enverrait un payload très volumineux pour saturer le serveur.
app.middleware("http")(limit_body_size)

# Middleware n°4 (personnalisé) : Monitoring pour Prometheus.
# Ce middleware intercepte chaque requête pour mettre à jour les métriques
# (nombre de requêtes, latence, etc.) qui seront ensuite exposées sur l'endpoint /metrics.
app.middleware("http")(monitoring_middleware)

# Middleware n°5 : Rate Limiting (Limitation de débit).
# Protège l'API contre les abus et les attaques par force brute en limitant
# le nombre de requêtes qu'une même adresse IP peut effectuer sur une période donnée.
limiter = Limiter(key_func=lambda request: request.headers.get("X-Forwarded-For", request.client.host))
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==============================================================================
# --- ÉTAPE 3 : GESTION DES ERREURS PERSONNALISÉES ---
# ===============================================================================

# Gestionnaire pour les erreurs de validation Pydantic (HTTP 422).
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Intercepte les erreurs levées par Pydantic lorsque les données d'une requête
    (ex: le corps JSON) ne correspondent pas au schéma attendu.

    Au lieu de la réponse par défaut de FastAPI, ceci renvoie une liste de messages
    d'erreur plus simples et plus directs, ce qui est plus facile à traiter
    pour un client frontend.
    """
    messages = [ err.get("msg") for err in exc.errors() ]
    return JSONResponse(
        status_code=422,
        content={"detail": messages}
    )

# Gestionnaire d'exception "fourre-tout".
@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    """
    Gère les exceptions non interceptées par d'autres gestionnaires.

    - Gère spécifiquement les `ValueError` (souvent levées pour des problèmes
      de logique métier) en les transformant en une erreur client 422 claire.
    - Pour toute autre exception inattendue (`RuntimeError`, etc.), il la propage
      (`raise exc`). FastAPI l'interceptera alors et générera une réponse
      HTTP 500 Internal Server Error, masquant les détails de l'erreur au client
      pour des raisons de sécurité.
    """
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)}
        )
    # Pour toutes les autres exceptions, on laisse FastAPI gérer et retourner une erreur 500.
    raise exc


# ==============================================================================
# --- ÉTAPE 4 : INCLUSION DES ROUTEURS ---
# ==============================================================================--
# On "branche" les fichiers contenant nos endpoints à l'application principale.
# Cela permet de découper le code en modules logiques (ex: tout ce qui est
# lié à la génération est dans `generation.py`).
app.include_router(generation.router)
app.include_router(monitoring.router)