from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.core.auth import authenticate_user, create_access_token, verify_jwt_token, create_user
from ..schemas import UserCreate, User
from database.core import get_db

router = APIRouter(tags=["Auth"])

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate, # <-- Utilise notre nouveau schéma pour valider les données d'entrée
    db: Session = Depends(get_db)
):
    """
    Crée un nouvel utilisateur dans la base de données.
    """
    try:
        # Appelle la fonction de création que nous avons définie à l'étape 1
        created_user = create_user(db=db, user_data=user_data)
        return created_user
    except HTTPException as e:
        # Propage les exceptions levées par create_user (ex: 409 Conflict)
        raise e
    except Exception as e:
        # Gère les autres erreurs potentielles
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue : {e}"
        )

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=400, detail="Identifiants invalides")
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def get_current_user(token_data: dict = Depends(verify_jwt_token)):
    return token_data
