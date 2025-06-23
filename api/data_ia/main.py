# api/data_ia/main.py

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.data_ia.routers import auth, generation, monitoring

app = FastAPI(
    title="Translation API",
    version="1.0",
    description="🔐 Authentification avec JWT"
)

# 1) Middleware custom pour injecter des headers de sécurité (HSTS, CSP, X-Frame-Options…)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # HSTS : un an, inclut les sous-domaines
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Bloquer l’affichage dans un <frame> ou <iframe>
    response.headers["X-Frame-Options"] = "DENY"

    # CSP différente pour Swagger UI (/docs), OpenAPI spec (/openapi.json) et ReDoc (/redoc)
    path = request.url.path
    if path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
        # Permettre inline scripts/styles nécessaires à Swagger UI et ReDoc
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
    else:
        # CSP stricte pour le reste de l’API
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

    return response

# 2) CORS — adapter allow_origins à ton domaine de prod et en dev inclure localhost
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

# 3) Limitation stricte de la taille du body (ici 10 KB max)
@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    max_bytes = 10 * 1024  # 10 Ko
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_bytes:
        return Response("Payload trop volumineux", status_code=413)
    return await call_next(request)

# 4) Monitoring middleware (existant)
app.middleware("http")(monitoring.monitoring_middleware)

# 5) Rate limiting global (slowapi)
limiter = Limiter(key_func=lambda request: request.headers.get("X-Forwarded-For", request.client.host))
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 6) Gestion des erreurs de validation Pydantic
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# 7) Inclusion des routers (auth, génération, monitoring)
app.include_router(auth.router)
app.include_router(generation.router)
app.include_router(monitoring.router)
