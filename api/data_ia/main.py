from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from api.data_ia.routers import auth, generation, monitoring


app = FastAPI(
    title="Translation API",
    version="1.0",
    description="""
    🔐 Authentification avec JWT
    """
)

# Middleware
app.middleware("http")(monitoring.monitoring_middleware)

# Rate limiting
limiter = Limiter(key_func=lambda request: request.headers.get("X-Forwarded-For", request.client.host))
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Gestion des erreurs
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# Routes
app.include_router(auth.router)
app.include_router(generation.router)
app.include_router(monitoring.router)