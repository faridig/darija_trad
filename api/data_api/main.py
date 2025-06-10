# api/data_api/main.py

from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from .db import get_db
from .schemas import Translation, TranslationCreate, TranslationUpdate
from .auth import authenticate_user, create_access_token, verify_jwt_token
from .models import User
from database.queries import TranslationQueries

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ----------------------
# CONFIGURATION FASTAPI
# ----------------------

app = FastAPI(
    title="Translation API",
    version="1.0",
    description="""
🔐 **Authentification avec JWT :**

1. Faites un `POST /login` avec vos identifiants.
2. Copiez le token retourné.
3. Cliquez sur 🔐 "Authorize" en haut à droite et collez `Bearer <token>`.

⚠️ Toutes les routes `/translations` nécessitent un token valide.
"""
)

# ----------------------
# MIDDLEWARES & LIMITEUR
# ----------------------

limiter = Limiter(key_func=lambda request: request.headers.get("X-Forwarded-For", request.client.host))
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ----------------------
# EXCEPTION HANDLER (422)
# ----------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

# ----------------------
# AUTHENTIFICATION
# ----------------------

@app.post("/login", tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authentifie un utilisateur et retourne un token d'accès JWT.
    """
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=400, detail="Identifiants invalides")
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me", tags=["Auth"])
def get_current_user(token_data: dict = Depends(verify_jwt_token)):
    """
    Retourne les informations extraites du token JWT actuel.
    """
    return token_data

# ----------------------
# ROUTES DE TRADUCTION (CRUD)
# ----------------------

@app.post("/translations", response_model=Translation, tags=["Translations"])
@limiter.limit("5/minute")
def create_translation(
    request: Request,
    data: TranslationCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    """
    Crée une nouvelle traduction (authentification requise).
    """
    try:
        return TranslationQueries.create(db, data.model_dump())
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur lors de la création")

@app.get("/translations", response_model=list[Translation], tags=["Translations"])
@limiter.limit("10/minute")
def get_all_translations(
    request: Request,
    source_lang: str = Query(None, description="Filtrer par langue source"),
    target_lang: str = Query(None, description="Filtrer par langue cible"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    """
    Récupère toutes les traductions, avec filtres optionnels.
    """
    return TranslationQueries.get_all(db, source_lang=source_lang, target_lang=target_lang)

@app.get("/translations/{id}", response_model=Translation, tags=["Translations"])
@limiter.limit("15/minute")
def get_translation(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    """
    Récupère une traduction spécifique par ID.
    """
    result = TranslationQueries.get_by_id(db, id)
    if result is None:
        raise HTTPException(status_code=404, detail="Traduction introuvable")
    return result

@app.put("/translations/{id}", response_model=Translation, tags=["Translations"])
@limiter.limit("3/minute")
def update_translation(
    request: Request,
    id: int,
    data: TranslationUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    """
    Met à jour une traduction existante.
    """
    updated = TranslationQueries.update(db, id, data.model_dump())
    if updated is None:
        raise HTTPException(status_code=404, detail="Traduction introuvable")
    return updated

@app.delete("/translations/{id}", response_model=Translation, tags=["Translations"])
@limiter.limit("2/minute")
def delete_translation(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    """
    Supprime une traduction par ID.
    """
    deleted = TranslationQueries.delete(db, id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Traduction introuvable")
    return deleted
