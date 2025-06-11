from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ...core.db import get_db
from ...core.auth import verify_jwt_token
from ..schemas import Translation, TranslationCreate, TranslationUpdate
from database.queries import TranslationQueries

router = APIRouter(tags=["Translations"])

@router.post("/translations", response_model=Translation)
def create_translation(
    request: Request,
    data: TranslationCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    try:
        return TranslationQueries.create(db, data.model_dump())
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur lors de la création")

@router.get("/translations", response_model=list[Translation])
def get_all_translations(
    request: Request,
    source_lang: str = Query(None),
    target_lang: str = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    return TranslationQueries.get_all(db, source_lang=source_lang, target_lang=target_lang)

@router.get("/translations/{id}", response_model=Translation)
def get_translation(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    result = TranslationQueries.get_by_id(db, id)
    if result is None:
        raise HTTPException(status_code=404, detail="Traduction introuvable")
    return result

@router.put("/translations/{id}", response_model=Translation)
def update_translation(
    request: Request,
    id: int,
    data: TranslationUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    updated = TranslationQueries.update(db, id, data.model_dump())
    if updated is None:
        raise HTTPException(status_code=404, detail="Traduction introuvable")
    return updated

@router.delete("/translations/{id}", response_model=Translation)
def delete_translation(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    deleted = TranslationQueries.delete(db, id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Traduction introuvable")
    return deleted
