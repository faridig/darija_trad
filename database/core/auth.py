

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from .models import User
from ..schemas import UserCreate

load_dotenv()

# Configuration JWT
SECRET_KEY = os.getenv("JWT_SECRET", "secret-for-dev-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Contexte de hachage pour les mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schéma HTTP Bearer pour Swagger UI (affiche "Bearer <token>" dans /docs)
bearer_scheme = HTTPBearer()

# ----------------------
# UTILITAIRES AUTH
# ----------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.hashed_password):
        return {"username": user.username}
    return None

def create_user(db: Session, user_data): # user_data sera de type UserCreate
    # 1. Vérifier si l'utilisateur existe déjà
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec ce nom existe déjà."
        )
    
    # 2. Hacher le mot de passe
    hashed_password = get_password_hash(user_data.password)
    
    # 3. Créer l'objet User pour la base de données
    db_user = User(
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    # 4. Ajouter, commiter et rafraîchir
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user



# ----------------------
# VÉRIFIE LE TOKEN JWT
# ----------------------

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token invalide")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
