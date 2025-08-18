# Fichier : api/data_api/main.py 
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.middleware.cors import CORSMiddleware

# Import des modules contenant les endpoints spécifiques
from .routers import auth, translations

# --- Étape 1: Initialisation de l'application FastAPI ---
# C'est le point d'entrée principal de notre API.
# Le titre et la description apparaîtront dans la documentation Swagger UI.
app = FastAPI(
    title="Data API",
    version="1.0",
    description="""
🔐 **Authentification avec JWT :**

1. Faites un `POST /login` avec vos identifiants.
2. Copiez le token retourné.
3. Cliquez sur 🔐 "Authorize" en haut à droite et collez `Bearer <token>`.

⚠️ Toutes les routes `/translations` nécessitent un token valide.
"""
)

# --- Étape 2: Configuration des Middlewares ---
# Les middlewares sont des fonctions qui traitent chaque requête avant qu'elle
# n'atteigne les endpoints, et chaque réponse avant qu'elle ne soit renvoyée.

# Middleware n°1 : CORS (Cross-Origin Resource Sharing)
# Permet à notre application frontend (tournant sur une autre adresse)
# de communiquer avec cette API. C'est une mesure de sécurité des navigateurs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Pour le développement local du frontend
        "http://12.34.56.78",     # Mettez ici l'IP publique de votre frontend déployé
    ],
    allow_credentials=True,
    allow_methods=["*"], # Autorise toutes les méthodes (GET, POST, PUT, DELETE...)
    allow_headers=["*"], # Autorise tous les en-têtes (comme Authorization)
)

# Middleware n°2 : Rate Limiting (Limitation de débit)
# Protège l'API contre les attaques par force brute ou les abus en limitant
# le nombre de requêtes qu'une même IP peut faire en un temps donné.
limiter = Limiter(key_func=lambda request: request.headers.get("X-Forwarded-For", request.client.host))
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- Étape 3: Configuration des Gestionnaires d'Exceptions Personnalisés ---
# Permet de contrôler le format des erreurs renvoyées par l'API.

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Ce gestionnaire intercepte les erreurs levées par Pydantic lorsque
    les données d'une requête ne correspondent pas au schéma attendu.
    Il renvoie une erreur 422 claire avec les détails du problème.
    """
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )


# --- Étape 4: Intégration des Routeurs ---
# On "branche" les fichiers contenant nos endpoints à l'application principale.
# Cela permet de garder le code organisé par fonctionnalité.
app.include_router(auth.router)
app.include_router(translations.router)