# database/core/auth.py

"""
Ce module centralise toute la logique liée à l'authentification et à la gestion
des utilisateurs. Il fournit des fonctions utilitaires pour :
- Le hachage et la vérification des mots de passe.
- La création et la validation des JSON Web Tokens (JWT).
- L'authentification et la création des utilisateurs en base de données.

Cette approche modulaire permet de réutiliser la même logique de sécurité
à travers différentes API (par exemple, data_api et ia_api).
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from .models import User

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# --- Configuration Globale de la Sécurité ---

# Clé secrète pour signer les JWT. Essentielle pour la sécurité.
# Chargée depuis les variables d'environnement pour ne pas l'exposer dans le code.
SECRET_KEY = os.getenv("JWT_SECRET", "secret-for-dev-only")

# Algorithme de signature utilisé pour les JWT. HS256 est un standard commun.
ALGORITHM = "HS256"

# Durée de validité par défaut d'un token d'accès.
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Contexte pour le hachage des mots de passe.
# Utilise l'algorithme bcrypt, qui est le standard actuel pour sa robustesse.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schéma d'authentification pour FastAPI et Swagger UI.
# Permet à Swagger de présenter une interface pour entrer le token "Bearer".
bearer_scheme = HTTPBearer()

# ---------------------------------
# FONCTIONS UTILITAIRES D'AUTHENTIFICATION
# ---------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare un mot de passe en clair avec sa version hachée.

    Args:
        plain_password (str): Le mot de passe fourni par l'utilisateur.
        hashed_password (str): Le mot de passe haché stocké en base de données.

    Returns:
        bool: True si les mots de passe correspondent, False sinon.
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Crée un nouveau JSON Web Token (JWT).

    Args:
        data (dict): Le dictionnaire de données (payload) à inclure dans le token.
                     Doit contenir une clé 'sub' (subject) pour l'identifiant de l'utilisateur.
        expires_delta (timedelta, optional): Durée de validité personnalisée. 
                                              Par défaut, utilise une durée de 15 minutes.

    Returns:
        str: Le token JWT encodé et signé.
    """
    to_encode = data.copy()
    # Définit la date d'expiration du token.
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    # Encode le payload avec la clé secrète et l'algorithme définis.
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str, db: Session):
    """
    Authentifie un utilisateur en vérifiant son nom d'utilisateur et son mot de passe.

    Args:
        username (str): Le nom d'utilisateur.
        password (str): Le mot de passe en clair.
        db (Session): La session de base de données.

    Returns:
        dict or None: Un dictionnaire avec le nom d'utilisateur si l'authentification réussit,
                      sinon None.
    """
    # 1. Recherche l'utilisateur dans la base de données.
    user = db.query(User).filter(User.username == username).first()
    # 2. Si l'utilisateur existe et que le mot de passe correspond, l'authentification est réussie.
    if user and verify_password(password, user.hashed_password):
        return {"username": user.username}
    # 3. Sinon, l'authentification échoue.
    return None

def get_password_hash(password: str) -> str:
    """
    Génère un hachage sécurisé pour un mot de passe.

    Args:
        password (str): Le mot de passe en clair.

    Returns:
        str: La version hachée du mot de passe.
    """
    return pwd_context.hash(password)

def create_user(db: Session, user_data): # user_data est un schéma Pydantic UserCreate
    """
    Crée un nouvel utilisateur dans la base de données.

    Args:
        db (Session): La session de base de données.
        user_data: Un objet contenant le `username` et le `password` du nouvel utilisateur.

    Raises:
        HTTPException: Leve une erreur 409 (Conflict) si le nom d'utilisateur existe déjà.

    Returns:
        User: L'objet utilisateur SQLAlchemy nouvellement créé.
    """
    # 1. Vérifier si l'utilisateur existe déjà pour garantir l'unicité du nom d'utilisateur.
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec ce nom existe déjà."
        )
    
    # 2. Hacher le mot de passe avant de le stocker. Ne JAMAIS stocker de mot de passe en clair.
    hashed_password = get_password_hash(user_data.password)
    
    # 3. Créer une nouvelle instance du modèle SQLAlchemy User.
    db_user = User(
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    # 4. Ajouter le nouvel utilisateur à la session, commiter la transaction, et rafraîchir
    #    l'instance pour obtenir les données générées par la BDD (comme l'ID).
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# ---------------------------------
# DÉPENDANCE FASTAPI POUR LA VÉRIFICATION DU TOKEN
# ---------------------------------

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Dépendance FastAPI pour protéger les endpoints.
    
    Cette fonction est utilisée dans les décorateurs de route pour exiger une
    authentification par token JWT. Elle extrait le token de l'en-tête `Authorization`,
    le décode et le valide.

    Args:
        credentials (HTTPAuthorizationCredentials): Injecté par FastAPI, contient le token.

    Raises:
        HTTPException: Leve une erreur 401 (Unauthorized) si le token est invalide,
                       malformé ou expiré.

    Returns:
        dict: Le payload du token décodé (contenant le `username`) si la validation réussit.
    """
    token = credentials.credentials
    try:
        # Tente de décoder le token avec la clé secrète et l'algorithme.
        # `jwt.decode` vérifie automatiquement la signature et la date d'expiration.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        # S'assure que le champ 'sub' (subject), qui contient le username, est présent.
        if not username:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        return {"username": username}
    
    # `jose` lève une JWTError pour toute sorte de problème (signature invalide, expiration, etc.).
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")