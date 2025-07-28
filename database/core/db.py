from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# --- 1. CHARGEMENT ROBUSTE DE LA CONFIGURATION ---

# Définir le chemin de la racine du projet de manière fiable.
# Par exemple, si ce fichier est dans /projets/darija_app_final/database/core,
# PROJECT_ROOT sera /projets/darija_app_final.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Construire le chemin complet vers le fichier .env.
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')

# Charger le fichier .env depuis ce chemin explicite s'il existe.
if os.path.exists(DOTENV_PATH):
    print(f"🔍 INFO: Chargement du fichier de configuration .env depuis {DOTENV_PATH}")
    load_dotenv(dotenv_path=DOTENV_PATH)
else:
    print(f"⚠️ AVERTISSEMENT: Fichier .env non trouvé à l'emplacement attendu : {DOTENV_PATH}")
    print("   Le programme se basera uniquement sur les variables d'environnement système.")

# --- 2. SÉLECTION INTELLIGENTE DE L'URL DE LA BASE DE DONNÉES ---

# On cherche d'abord une URL pour le développement LOCAL.
# Cette variable doit être définie dans votre .env pour le travail en local.
LOCAL_DB_URL = os.getenv("DATABASE_URL")

# On cherche ensuite l'URL de PRODUCTION (Supabase).
PROD_DB_URL = os.getenv("SUPABASE_URL")

# Logique de sélection : priorité au local.
if LOCAL_DB_URL:
    FINAL_DATABASE_URL = LOCAL_DB_URL
    print("✅ Mode DÉVELOPPEMENT LOCAL détecté. Utilisation de DATABASE_URL.")
elif PROD_DB_URL:
    FINAL_DATABASE_URL = PROD_DB_URL
    print("✅ Mode PRODUCTION détecté. Utilisation de SUPABASE_URL.")
else:
    # Si aucune des deux n'est trouvée, on met la variable à None.
    FINAL_DATABASE_URL = None
    print("❌ ERREUR DE CONFIG: Aucune URL de base de données (DATABASE_URL ou SUPABASE_URL) n'a été trouvée.")


# --- 3. INITIALISATION "LAZY" (PARESSEUSE) DE SQLAlchemy ---

_engine = None
_SessionLocal = None
Base = declarative_base()


def get_engine():
    """Crée l'engine une seule fois (singleton pattern)."""
    global _engine
    if _engine is None:
        # Vérification critique avant de tenter de créer l'engine.
        if not FINAL_DATABASE_URL:
            raise ValueError("Configuration de base de données manquante. Veuillez définir DATABASE_URL ou SUPABASE_URL.")
        
        print(f"🔗 Création de l'engine de base de données...")
        _engine = create_engine(FINAL_DATABASE_URL)
    return _engine


def get_session_local():
    """Crée la factory de session une seule fois."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


# --- 4. DÉPENDANCE FastAPI POUR LA GESTION DES SESSIONS ---

def get_db():
    """
    Dépendance FastAPI qui fournit une session de base de données par requête
    et garantit sa fermeture après usage.
    """
    # On récupère la factory de session.
    SessionLocal = get_session_local()
    
    # On crée une nouvelle session pour cette requête spécifique.
    db = SessionLocal()
    try:
        # On fournit la session à la fonction de la route.
        yield db
    finally:
        # Après la fin de la requête (même en cas d'erreur), on ferme la session.
        # Cela la remet dans le pool de connexions pour être réutilisée.
        db.close()