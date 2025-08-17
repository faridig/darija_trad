from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone  # NOUVEAU: Import pour gérer la date et l'heure

# Vos imports existants restent inchangés
from database.core.auth import authenticate_user, create_access_token, verify_jwt_token, create_user
from ..schemas import UserCreate, User
from database.core import get_db
from database.core.models import User as UserModel # NOUVEAU: Import du modèle SQLAlchemy pour pouvoir modifier la table

router = APIRouter(tags=["Auth"])

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Crée un nouvel utilisateur dans la base de données.
    """
    try:
        created_user = create_user(db=db, user_data=user_data)
        return created_user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue : {e}"
        )

# --- C'est ici que la modification a lieu ---
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Étape 1: Authentification (inchangée)
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=400, detail="Identifiants invalides")

    # NOUVEAU: Début de la mise à jour de last_login
    try:
        db_user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
        if db_user:
            db_user.last_login = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        db.rollback()
        # On log l'erreur mais on ne bloque pas la connexion
        print(f"AVERTISSEMENT: Échec de la mise à jour de last_login pour l'utilisateur {form_data.username}. Erreur: {e}")
    # NOUVEAU: Fin de la mise à jour

    # Étape 2: Création du token (inchangée)
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}
# --- Fin de la modification ---

@router.get("/me")
def get_current_user(token_data: dict = Depends(verify_jwt_token)):
    return token_data