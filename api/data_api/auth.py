# api/data_api/auth.py

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from .db import get_db
from .models import User

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
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.hashed_password):
        return {"username": user.username}
    return None

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
