from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# On ne définit QUE l'URL ici. PAS l'engine.
DATABASE_URL = os.getenv("SUPABASE_URL")

# On initialise l'engine et la session à None.
# Ils seront créés à la volée.
_engine = None
_SessionLocal = None
Base = declarative_base()

def get_engine():
    """Crée l'engine une seule fois."""
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise ValueError("La variable d'environnement SUPABASE_URL n'est pas définie.")
        _engine = create_engine(DATABASE_URL)
    return _engine

def get_session_local():
    """Crée la factory de session une seule fois."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal

# Dépendance FastAPI (MODIFIÉE)
def get_db():
    """
    Dépendance FastAPI qui fournit une session de base de données.
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()