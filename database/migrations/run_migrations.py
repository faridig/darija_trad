# Fichier : database/migrations/run_migrations.py
# Rôle : Orchestrateur principal pour initialiser une base de données locale à partir de zéro.
# Ce script est le point d'entrée pour créer le schéma, insérer les données et configurer l'admin.

import psycopg2
from dotenv import load_dotenv
import sys
import os

# --- ÉTAPE 1 : CONFIGURATION DU CHEMIN D'ACCÈS (PYTHONPATH) ---
# Objectif : Permettre au script de trouver et d'importer des modules d'autres
# dossiers du projet (comme 'database.insert_admin'). C'est essentiel pour que
# le script puisse être exécuté depuis n'importe où.

# On calcule le chemin absolu de la racine du projet (deux niveaux au-dessus de ce fichier)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# On l'ajoute au `sys.path` (la liste des dossiers où Python cherche les modules)
# seulement s'il n'y est pas déjà, pour éviter les doublons.
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"🔧 INFO – Racine du projet ajoutée à sys.path : {project_root}")

# Maintenant que le chemin est configuré, on peut importer nos modules en toute sécurité.
from database.insert_admin import insert_admin
from database.insert_data import insert_translations

# --- ÉTAPE 2 : CHARGEMENT DE LA CONFIGURATION ---
# Objectif : Récupérer les identifiants de la base de données depuis un fichier .env
# pour éviter de les écrire en dur dans le code (bonne pratique de sécurité).
print("📄 INFO – Chargement des variables d'environnement...")
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# --- ÉTAPE 3 : DÉFINITION DE LA SÉQUENCE DE MIGRATION ---
# Objectif : Lister les scripts SQL à exécuter dans un ordre précis et immuable
# pour garantir que la base de données est construite de manière cohérente.
# Par exemple, on doit créer les tables avant d'y ajouter des contraintes.
print("📋 INFO – Définition de la séquence de migration...")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MIGRATIONS = [
    os.path.join(BASE_DIR, '001_create_translations.sql'), # Crée la table des traductions
    os.path.join(BASE_DIR, '002_create_users_table.sql'),    # Crée la table des utilisateurs
    os.path.join(BASE_DIR, '003_add_unique_constraint.sql'), # Ajoute une contrainte à la table des traductions
    os.path.join(BASE_DIR, '004_add_timestamps_users.sql')  # Ajoute des colonnes à la table des users pour le RGPD
]

# --- ÉTAPE 4 : EXÉCUTION DE L'ORCHESTRATION ---
# Objectif : Se connecter à la base de données et exécuter toutes les étapes
# dans une transaction pour garantir que si une étape échoue, rien n'est appliqué.
try:
    print(f"🔗 INFO – Connexion à la base de données '{DB_NAME}' sur {DB_HOST}...")
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    # Un curseur est l'objet qui permet d'exécuter des commandes SQL.
    cur = conn.cursor()
    print("✅ INFO – Connexion réussie.")

    # 4a. Exécution des migrations pour créer le schéma
    print("\n--- DÉBUT : Application du schéma de la base de données ---")
    for migration_file in MIGRATIONS:
        print(f"    - Exécution de : {os.path.basename(migration_file)}...")
        with open(migration_file, 'r') as file:
            sql = file.read()
            cur.execute(sql)
    # Le `commit` valide toutes les modifications faites pendant la boucle.
    conn.commit()
    print("--- FIN : Schéma appliqué avec succès ---\n")

    # 4b. Insertion des données (peuplement)
    print("--- DÉBUT : Insertion des données ---")
    insert_translations() # Appel de la fonction de insert_data.py
    insert_admin()        # Appel de la fonction de insert_admin.py
    print("--- FIN : Données insérées avec succès ---\n")

except Exception as e:
    print(f"❌ ERREUR – Une erreur est survenue : {e}")
    # En cas d'erreur, on annule toutes les modifications qui n'ont pas été "committées".
    # C'est une sécurité essentielle pour ne pas laisser la BDD dans un état incohérent.
    if 'conn' in locals() and conn:
        conn.rollback()
    print("🔒 INFO – Rollback effectué. Aucune modification n'a été sauvegardée.")

finally:
    # Cette section s'exécute TOUJOURS, que le script ait réussi ou échoué.
    # On s'assure de bien fermer la connexion à la base de données pour libérer les ressources.
    if 'cur' in locals() and cur:
        cur.close()
    if 'conn' in locals() and conn:
        conn.close()
    print("🔌 INFO – Connexion à la base de données fermée.")