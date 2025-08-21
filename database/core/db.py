# database/core/db.py

"""
Point central pour la configuration de la base de données, la gestion de la connexion
et la création des sessions transactionnelles avec SQLAlchemy.

Ce module est conçu pour être :
- Robuste : Il gère les environnements de développement local et de production.
- Efficace : Il utilise un pattern de "lazy initialization" pour ne créer la connexion
  que lorsque c'est nécessaire.
- Intégré : Il fournit une dépendance FastAPI (`get_db`) pour une gestion
  sécurisée et automatique des sessions par requête.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# --- 1. CHARGEMENT ROBUSTE DE LA CONFIGURATION D'ENVIRONNEMENT ---

# Calcule le chemin absolu de la racine du projet pour trouver le fichier .env de manière fiable,
# peu importe d'où le script est exécuté.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Construit le chemin complet vers le fichier .env à la racine du projet.
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')

# Charge les variables du fichier .env dans l'environnement du processus.
# S'il n'existe pas, le programme peut quand même fonctionner si les variables
# d'environnement sont fournies par le système (ex: dans un conteneur Docker).
if os.path.exists(DOTENV_PATH):
    print(f"🔍 INFO: Chargement du fichier de configuration .env depuis {DOTENV_PATH}")
    load_dotenv(dotenv_path=DOTENV_PATH)
else:
    print(f"⚠️ AVERTISSEMENT: Fichier .env non trouvé à l'emplacement attendu : {DOTENV_PATH}")
    print("   Le programme se basera uniquement sur les variables d'environnement système.")

# --- 2. SÉLECTION INTELLIGENTE DE L'URL DE LA BASE DE DONNÉES ---

# Lit la variable d'environnement pour la base de données de développement local.
LOCAL_DB_URL = os.getenv("DATABASE_URL")

# Lit la variable d'environnement pour la base de données de production (hébergée sur Supabase).
PROD_DB_URL = os.getenv("SUPABASE_URL")

# Logique de sélection qui donne la priorité à l'environnement local.
# C'est une pratique courante pour faciliter le développement et les tests.
if LOCAL_DB_URL:
    FINAL_DATABASE_URL = LOCAL_DB_URL
    print("✅ Mode DÉVELOPPEMENT LOCAL détecté. Utilisation de DATABASE_URL.")
elif PROD_DB_URL:
    FINAL_DATABASE_URL = PROD_DB_URL
    print("✅ Mode PRODUCTION détecté. Utilisation de SUPABASE_URL.")
else:
    # Si aucune URL n'est configurée, on lève une erreur plus tard pour éviter
    # que l'application ne démarre avec une configuration invalide.
    FINAL_DATABASE_URL = None
    print("❌ ERREUR DE CONFIG: Aucune URL de base de données (DATABASE_URL ou SUPABASE_URL) n'a été trouvée.")


# --- 3. INITIALISATION "LAZY" (PARESSEUSE) DES COMPOSANTS SQLAlchemy ---

# On initialise les variables globales à None. Elles ne seront créées
# qu'au premier appel des fonctions `get_engine` et `get_session_local`.
# C'est un pattern "singleton" qui évite de créer des connexions inutilement.
_engine = None
_SessionLocal = None

# Base déclarative pour les modèles ORM de SQLAlchemy.
# Tous nos modèles (User, Translation) hériteront de cette classe.
Base = declarative_base()


def get_engine():
    """
    Crée et retourne l'engine SQLAlchemy.
    
    Utilise un pattern singleton ("lazy initialization") pour s'assurer que l'objet `engine`,
    qui gère le pool de connexions à la base de données, n'est créé qu'une seule fois
    au cours de la vie de l'application.

    Raises:
        ValueError: Si aucune URL de base de données n'a été configurée.

    Returns:
        sqlalchemy.engine.Engine: L'instance de l'engine SQLAlchemy.
    """
    global _engine
    if _engine is None:
        # Vérification critique : on ne peut pas continuer sans URL de BDD.
        if not FINAL_DATABASE_URL:
            raise ValueError("Configuration de base de données manquante. Veuillez définir DATABASE_URL ou SUPABASE_URL.")
        
        print(f"🔗 Création de l'engine de base de données...")
        _engine = create_engine(FINAL_DATABASE_URL)
    return _engine


def get_session_local():
    """
    Crée et retourne la factory de sessions SQLAlchemy.

    Comme pour `get_engine`, cette fonction utilise un pattern singleton pour créer
    la classe `SessionLocal` une seule fois. Cette classe sera ensuite utilisée
    pour créer des sessions de base de données individuelles pour chaque requête.

    Returns:
        sqlalchemy.orm.sessionmaker: Une factory pour créer des objets Session.
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


# --- 4. DÉPENDANCE FastAPI POUR LA GESTION DES SESSIONS PAR REQUÊTE ---

def get_db():
    """
    Dépendance FastAPI pour la gestion du cycle de vie d'une session de base de données.

    Cette fonction est un "générateur" qui sera "injecté" par FastAPI dans chaque
    endpoint qui en a besoin. Elle garantit qu'une session est créée au début de la
    requête et qu'elle est toujours fermée à la fin, même en cas d'erreur.

    Yields:
        sqlalchemy.orm.Session: Une session de base de données transactionnelle.
    """
    # 1. Récupère la factory de session.
    SessionLocal = get_session_local()
    
    # 2. Crée une nouvelle session à partir de la factory pour cette requête spécifique.
    db = SessionLocal()
    try:
        # 3. Le mot-clé `yield` passe la session au code de l'endpoint.
        #    L'exécution de cette fonction est mise en pause ici jusqu'à ce que
        #    l'endpoint ait fini son travail.
        yield db
    finally:
        # 4. Cette partie est exécutée APRÈS que la réponse de l'endpoint a été envoyée.
        #    Elle garantit que la session est fermée, ce qui libère la connexion et la
        #    remet dans le pool de connexions pour être réutilisée. C'est crucial
        #    pour éviter les fuites de ressources.
        db.close()