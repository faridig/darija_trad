from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, translations

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Pourr le développement local du frontend
        "http://127.0.0.1:5173",
        "http://4.178.232.175", #fronted azure
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"], # Autorisez toutes les méthodes que vous utilisez
    allow_headers=["Authorization", "Content-Type"],
)

# Rate limiting
limiter = Limiter(key_func=lambda request: request.headers.get("X-Forwarded-For", request.client.host))
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Validation handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# Importer les routes
app.include_router(auth.router)
app.include_router(translations.router)
