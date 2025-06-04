from fastapi import FastAPI, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from database.queries import TranslationQueries
from .db import SessionLocal
from .schemas import Translation, TranslationCreate, TranslationUpdate

# SlowAPI - Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Authentification JWT
from fastapi.security import OAuth2PasswordRequestForm
from .auth import authenticate_user, create_access_token, verify_jwt_token

# Création du Limiteur (IP-based)
limiter = Limiter(key_func=get_remote_address)

# Création de l'application FastAPI
app = FastAPI(title="Translation API", version="1.0")

# Intégration du rate limiter dans l'application
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ----------------------
# AUTHENTIFICATION ROUTE
# ----------------------

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Identifiants invalides")

    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# ----------------------
# DATABASE SESSION
# ----------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------
# ROUTES PROTÉGÉES PAR JWT
# ----------------------

@app.post("/translations", response_model=Translation)
@limiter.limit("5/minute")
def create_translation(
    request: Request,
    data: TranslationCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    return TranslationQueries.create(db, data.model_dump())


@app.get("/translations", response_model=list[Translation])
@limiter.limit("10/minute")
def get_all_translations(
    request: Request,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    return TranslationQueries.get_all(db)


@app.get("/translations/{id}", response_model=Translation)
@limiter.limit("15/minute")
def get_translation(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    result = TranslationQueries.get_by_id(db, id)
    if result is None:
        raise HTTPException(status_code=404, detail="Translation not found")
    return result


@app.put("/translations/{id}", response_model=Translation)
@limiter.limit("3/minute")
def update_translation(
    request: Request,
    id: int,
    data: TranslationUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    updated = TranslationQueries.update(db, id, data.model_dump())
    if updated is None:
        raise HTTPException(status_code=404, detail="Translation not found")
    return updated


@app.delete("/translations/{id}", response_model=Translation)
@limiter.limit("2/minute")
def delete_translation(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    deleted = TranslationQueries.delete(db, id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Translation not found")
    return deleted
