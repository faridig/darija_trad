# database/maintenance/cleanup_inactive_users.py

import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from sqlalchemy import or_
from sqlalchemy.orm import Session

# ==============================================================================
# SECTION 1 : CONFIGURATION INITIALE
# ==============================================================================

# Configure le logger pour afficher des messages clairs et horodatés dans la console.
# C'est une bonne pratique pour suivre l'exécution des scripts en production.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ajoute dynamiquement la racine du projet au PYTHONPATH.
# Cela permet au script d'être exécuté depuis n'importe quel endroit
# tout en pouvant importer des modules du projet comme 'database.core'.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logging.info(f"Racine du projet ajoutée à sys.path : {project_root}")

# Importe les modules nécessaires APRÈS la configuration du path.
from database.core.db import get_session_local
from database.core.models import User

# Charge les variables d'environnement (identifiants BDD, nom de l'admin)
# depuis le fichier .env situé à la racine du projet.
load_dotenv(os.path.join(project_root, '.env'))

# Constante de configuration pour la politique de conservation des données.
# C'est le seul endroit à modifier si la politique change (ex: passer à 5 ans).
INACTIVITY_PERIOD_DAYS = 3 * 365


# ==============================================================================
# SECTION 2 : LOGIQUE MÉTIER
# ==============================================================================

def cleanup_inactive_users():
    """
    Script de maintenance pour la conformité RGPD.

    Cette fonction identifie et supprime les comptes utilisateurs inactifs
    de la base de données, en se basant sur une période de conservation définie.
    Elle garantit la protection du compte administrateur pour éviter toute
    suppression accidentelle.

    Le processus est le suivant :
    1. Établit une connexion à la base de données.
    2. Calcule une date "limite" d'inactivité (date actuelle - période de conservation).
    3. Construit une requête SQLAlchemy pour sélectionner les utilisateurs inactifs.
    4. Exclut l'administrateur de cette sélection.
    5. Affiche les utilisateurs à supprimer (pour la traçabilité et le débogage).
    6. Exécute la suppression et valide la transaction.
    7. Gère les erreurs et assure la fermeture de la connexion.
    """
    logging.info("🚀 Démarrage du script de nettoyage des utilisateurs inactifs.")
    
    # Récupère la factory de session pour créer une session de BDD.
    SessionLocal = get_session_local()
    db: Session = SessionLocal()

    try:
        # --- Étape A: Calculer la date limite d'inactivité ---
        # `timezone.utc` est utilisé pour éviter les problèmes liés aux fuseaux horaires.
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=INACTIVITY_PERIOD_DAYS)
        logging.info(f"La date limite d'inactivité est fixée au : {cutoff_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        # --- Étape B: Protéger le compte administrateur ---
        # Le nom de l'admin est récupéré depuis les variables d'environnement.
        admin_username = os.getenv("ADMIN_USERNAME")
        if not admin_username:
            logging.warning("⚠️ La variable ADMIN_USERNAME n'est pas définie. La protection de l'admin est désactivée.")

        # --- Étape C: Construire la requête de sélection ---
        # La requête cible les utilisateurs qui remplissent l'une des deux conditions suivantes :
        #   1. `User.last_login < cutoff_date` : L'utilisateur s'est connecté, mais il y a plus de 3 ans.
        #   2. `(User.last_login == None) & (User.created_at < cutoff_date)` : L'utilisateur ne s'est JAMAIS connecté
        #      ET son compte a été créé il y a plus de 3 ans.
        query = db.query(User).filter(
            or_(
                User.last_login < cutoff_date,
                (User.last_login == None) & (User.created_at < cutoff_date)
            )
        )

        # Ajoute une clause `WHERE username != 'admin'` à la requête si l'admin est défini.
        if admin_username:
            query = query.filter(User.username != admin_username)
            logging.info(f"L'utilisateur admin '{admin_username}' est protégé et ne sera pas supprimé.")

        # --- Étape D: Exécution sécurisée (afficher avant de supprimer) ---
        # `query.all()` exécute la requête SELECT pour prévisualiser les cibles.
        users_to_delete = query.all()

        if not users_to_delete:
            logging.info("✅ Aucun utilisateur inactif à supprimer. Tâche terminée.")
            return # Sort de la fonction si il n'y a rien à faire.

        # Loggue chaque utilisateur qui va être supprimé pour la traçabilité.
        logging.warning(f" trouvé(s) {len(users_to_delete)} utilisateur(s) inactif(s) à supprimer :")
        for user in users_to_delete:
            # Affiche la dernière date d'activité connue (soit le login, soit la création du compte).
            last_active = user.last_login or user.created_at
            logging.warning(f"  - Utilisateur: {user.username} (ID: {user.id}), dernière activité: {last_active.strftime('%Y-%m-%d')}")
        
        # Supprime les utilisateurs identifiés par la requête.
        # `synchronize_session=False` est une optimisation pour les suppressions en masse.
        deleted_count = query.delete(synchronize_session=False)
        
        # Valide la transaction. Ce n'est qu'à ce moment que les données sont réellement supprimées.
        db.commit()

        logging.info(f"✅ Opération réussie : {deleted_count} utilisateur(s) inactif(s) ont été supprimé(s).")

    except Exception as e:
        # En cas d'erreur (ex: la BDD est inaccessible), on annule toutes les modifications.
        logging.error(f"❌ Une erreur est survenue : {e}")
        db.rollback()
    finally:
        # Quoi qu'il arrive (succès ou erreur), on ferme la connexion à la BDD
        # pour libérer les ressources.
        logging.info("Fermeture de la session de base de données.")
        db.close()


# ==============================================================================
# SECTION 3 : POINT D'ENTRÉE
# ==============================================================================

if __name__ == "__main__":
    # Ce bloc de code n'est exécuté que si on lance le script directement
    # avec la commande `python -m database.maintenance.cleanup_inactive_users`.
    cleanup_inactive_users()