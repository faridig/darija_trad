# api/data_api/routers/translations.py 

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

# Importation des modules fondamentaux
from database.core.db import get_db
from database.core.auth import verify_jwt_token
from ..schemas import Translation, TranslationCreate, TranslationUpdate
from database.queries import TranslationQueries # <-- Notre couche d'abstraction de données

# --- Création du Routeur pour les Traductions ---
# Ce routeur gère toutes les opérations CRUD sur le corpus.
router = APIRouter(tags=["Translations"])


# --- Dépendance commune pour la sécurité ---
# Pour éviter de répéter `_: dict = Depends(verify_jwt_token)` dans chaque fonction,
# on pourrait définir une dépendance globale pour ce routeur.
# Mais pour la clarté, le répéter est aussi une bonne option.
# La variable `_` est une convention Python pour dire "cette variable est nécessaire
# pour que la dépendance s'exécute, mais je n'utiliserai pas sa valeur de retour".


@router.post("/translations", response_model=Translation)
def create_translation(
    request: Request,
    data: TranslationCreate,
    db: Session = Depends(get_db),
    # Chaque requête à ce routeur doit fournir un token JWT valide.
    _: dict = Depends(verify_jwt_token)
):
    """Crée une nouvelle entrée de traduction dans la base de données."""
    try:
        # On délègue TOUTE la logique de création à notre couche de requêtes.
        # L'endpoint reste simple et ne connaît rien au SQL.
        return TranslationQueries.create(db, data.model_dump())
    except Exception:
        # Gestion d'erreur générique si la création en base échoue.
        raise HTTPException(status_code=500, detail="Erreur lors de la création")


@router.get("/translations", response_model=list[Translation])
def get_all_translations(
    request: Request,
    # FastAPI gère automatiquement les paramètres de requête optionnels.
    # ex: /translations?source_lang=fr
    source_lang: str = Query(None),
    target_lang: str = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    """Récupère une liste de traductions, avec filtres optionnels."""
    # On passe simplement les filtres à notre couche de requêtes.
    return TranslationQueries.get_all(db, source_lang=source_lang, target_lang=target_lang)


@router.get("/translations/{id}", response_model=Translation)
def get_translation(
    request: Request,
    id: int, # FastAPI valide que `id` est bien un entier.
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)
):
    """Récupère une traduction spécifique par son ID."""
    result = TranslationQueries.get_by_id(db, id)
    # Si la couche de requêtes ne trouve rien, on renvoie une erreur 404.
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
    """Met à jour une traduction existante."""
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
    """Supprime une traduction existante."""
    deleted = TranslationQueries.delete(db, id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Traduction introuvable")
    return deleted