import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from sqlalchemy import or_
from sqlalchemy.orm import Session

# --- Configuration du Logging ---
# Affiche des messages clairs dans la console lors de l'exécution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Étape 1: Rendre les modules du projet importables ---
# Ajoute la racine du projet au chemin de recherche Python pour trouver 'database.core'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logging.info(f"Racine du projet ajoutée à sys.path : {project_root}")

# --- Étape 2: Importer les modules du projet ---
from database.core.db import get_session_local
from database.core.models import User

# --- Étape 3: Charger la configuration ---
# Charge les variables depuis le fichier .env situé à la racine du projet
load_dotenv(os.path.join(project_root, '.env'))

# Définir la durée de conservation. Ici, 3 ans.
# C'est le seul endroit à modifier si votre politique de conservation change.
INACTIVITY_PERIOD_DAYS = 3 * 365

def cleanup_inactive_users():
    """
    Identifie et supprime les utilisateurs inactifs de la base de données,
    tout en protégeant le compte administrateur.
    """
    logging.info("🚀 Démarrage du script de nettoyage des utilisateurs inactifs.")
    
    SessionLocal = get_session_local()
    db: Session = SessionLocal()

    try:
        # --- Étape 4: Calculer la date limite d'inactivité ---
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=INACTIVITY_PERIOD_DAYS)
        logging.info(f"La date limite d'inactivité est fixée au : {cutoff_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        # --- Étape 5: Protéger le compte administrateur ---
        # Récupérer le nom de l'admin depuis .env pour ne jamais le supprimer
        admin_username = os.getenv("ADMIN_USERNAME")
        if not admin_username:
            logging.warning("⚠️ La variable ADMIN_USERNAME n'est pas définie. La protection de l'admin est désactivée.")

        # --- Étape 6: Construire la requête de sélection des utilisateurs à supprimer ---
        # Un utilisateur est inactif si :
        #   - Sa dernière connexion est plus ancienne que la date limite.
        #   OU
        #   - Il ne s'est jamais connecté ET son compte a été créé avant la date limite.
        query = db.query(User).filter(
            or_(
                User.last_login < cutoff_date,
                (User.last_login == None) & (User.created_at < cutoff_date)
            )
        )

        # Appliquer la protection de l'admin à la requête
        if admin_username:
            query = query.filter(User.username != admin_username)
            logging.info(f"L'utilisateur admin '{admin_username}' est protégé et ne sera pas supprimé.")

        # --- Étape 7: Exécution sécurisée (afficher avant de supprimer) ---
        users_to_delete = query.all()

        if not users_to_delete:
            logging.info("✅ Aucun utilisateur inactif à supprimer. Tâche terminée.")
            return

        logging.warning(f" trouvé(s) {len(users_to_delete)} utilisateur(s) inactif(s) à supprimer :")
        for user in users_to_delete:
            last_active = user.last_login or user.created_at
            logging.warning(f"  - Utilisateur: {user.username} (ID: {user.id}), dernière activité: {last_active.strftime('%Y-%m-%d')}")
        
        # Confirmation avant suppression (sécurité supplémentaire)
        # Vous pouvez décommenter ces lignes si vous voulez une confirmation manuelle
        # confirm = input("Voulez-vous vraiment supprimer ces utilisateurs ? (oui/non): ")
        # if confirm.lower() != 'oui':
        #     logging.info("Opération annulée par l'utilisateur.")
        #     return

        # Supprimer les utilisateurs
        deleted_count = query.delete(synchronize_session=False)
        db.commit()

        logging.info(f"✅ Opération réussie : {deleted_count} utilisateur(s) inactif(s) ont été supprimé(s).")

    except Exception as e:
        logging.error(f"❌ Une erreur est survenue : {e}")
        db.rollback()
    finally:
        logging.info("Fermeture de la session de base de données.")
        db.close()


if __name__ == "__main__":
    # Ce bloc est exécuté seulement si on lance le script directement
    cleanup_inactive_users()