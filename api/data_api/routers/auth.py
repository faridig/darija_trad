# Fichier : api/data_api/routers/auth.py 

from fastapi import APIRouter, Depends, HTTPException, status, Request 
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone

# --- Importation des modules de la couche /core ---
# On importe la logique métier partagée pour la garder centralisée.
from database.core.auth import authenticate_user, create_access_token, verify_jwt_token, create_user
from ..schemas import UserCreate, User
from database.core import get_db
from database.core.models import User as UserModel

from ..limiter import limiter


# --- Création d'un "Routeur" ---
# Un routeur est un mini-groupe d'endpoints. Cela permet d'organiser le code.
# Le tag "Auth" regroupera ces endpoints dans la documentation Swagger.
router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour") # Limite stricte : 10 inscriptions par heure par IP
def register(
    request: Request,
    user_data: UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Endpoint pour l'inscription d'un nouvel utilisateur.
    - Valide les données d'entrée grâce au schéma Pydantic `UserCreate`.
    - Délègue la création de l'utilisateur à la fonction `create_user` de la couche /core.
    - Gère les exceptions (ex: utilisateur déjà existant) pour renvoyer des erreurs claires.
    """
    try:
        # On délègue la logique métier à la fonction centralisée
        created_user = create_user(db=db, user_data=user_data)
        return created_user
    except HTTPException as e:
        # Si une erreur métier connue (ex: 409 Conflict) est levée, on la propage.
        raise e
    except Exception as e:
        # Pour toute autre erreur inattendue, on renvoie une erreur 500 générique.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue : {e}"
        )


@router.post("/login")
@limiter.limit("20/minute") # Limite plus permissive, mais protège contre le brute-force rapide

def login(
    # FastAPI utilise ce `Depends` pour extraire `username` et `password`
    # d'une requête de type "form-data", le standard pour OAuth2.
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint pour la connexion d'un utilisateur et la génération d'un token JWT.
    """
    # Étape 1: On délègue l'authentification à la fonction partagée `authenticate_user`.
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=400, detail="Identifiants invalides")

    # Étape 2: Mise à jour du timestamp `last_login` (Conformité RGPD).
    # Cette logique est spécifique à l'action de login, elle reste donc ici.
    try:
        # On récupère l'objet utilisateur SQLAlchemy pour pouvoir le modifier.
        db_user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
        if db_user:
            db_user.last_login = datetime.now(timezone.utc)
            db.commit() # On sauvegarde le changement en base.
    except Exception as e:
        db.rollback() # En cas d'erreur, on annule la transaction.
        # On ne bloque pas la connexion, mais on log l'erreur côté serveur.
        print(f"AVERTISSEMENT: Échec de la mise à jour de last_login pour l'utilisateur {form_data.username}. Erreur: {e}")

    # Étape 3: On délègue la création du token JWT à la fonction partagée.
    token = create_access_token(data={"sub": user["username"]})
    
    # On renvoie le token au client.
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def get_current_user(
    # --- La sécurité est ici ---
    # `Depends(verify_jwt_token)` signifie que cette fonction ne sera exécutée
    # que si la fonction `verify_jwt_token` (de /core) réussit.
    # Si le token est invalide ou manquant, `verify_jwt_token` lèvera une
    # exception 401 et le code ci-dessous ne sera jamais atteint.
    token_data: dict = Depends(verify_jwt_token)
):
    """
    Endpoint protégé qui renvoie les informations de l'utilisateur connecté.
    Permet au frontend de vérifier que le token est toujours valide.
    """
    return token_data