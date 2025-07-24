# api/ia_api/main.py

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Test de déclenchement du pipeline CI/CD

# Routes
from api.ia_api.routers import auth, generation, monitoring

# Middlewares personnalisés
from api.ia_api.middlewares import (
    add_security_headers,
    limit_body_size,
    monitoring_middleware
)

# Initialisation FastAPI
app = FastAPI(
    title="Translation API",
    version="1.0",
    description="🔐 Authentification avec JWT",
    swagger_ui_parameters={
        "jsonEditor": False,
        "defaultModelRendering": "model",
    },
)

# 1) Sécurité HTTP headers
app.middleware("http")(add_security_headers)

# 2) CORS — autoriser l'origine locale et celle du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mon-frontend.exemple.com",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"]
)

# 3) Limitation stricte de la taille du body (ex: max 10 KB)
app.middleware("http")(limit_body_size)

# 4) Middleware de monitoring (Prometheus + logging)
app.middleware("http")(monitoring_middleware)

# 5) Rate limiting global (SlowAPI)
limiter = Limiter(key_func=lambda request: request.headers.get("X-Forwarded-For", request.client.host))
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 6) Gestion des erreurs de validation (FastAPI + Pydantic)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # On ne garde que les messages de chaque erreur Pydantic,
    # pour éviter d'essayer de serialiser un Pattern, un ValueError, etc.
    messages = [ err.get("msg") for err in exc.errors() ]
    return JSONResponse(
        status_code=422,
        content={"detail": messages}
    )


# 7) Inclusion des routes principales
app.include_router(auth.router)
app.include_router(generation.router)
app.include_router(monitoring.router)


@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    # Si c'est un ValueError (nos validations Pydantic),
    # on renvoie 422 avec le message de l'erreur.
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)}
        )
    # Tout le reste, on le remonte pour que FastAPI/Gestionnaire dédié le traite.
    raise exc

    return JSONResponse(
    status_code=500,
    content={"detail": "Internal Server Error"}
)