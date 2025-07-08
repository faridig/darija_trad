print("🔍 DEBUG – run_migrations.py démarre ici")

import psycopg2
from dotenv import load_dotenv
import sys, os
# 🔧 S’assurer que la racine du projet est dans sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print("🔧 DEBUG – project_root ajouté à sys.path :", project_root)
from database.insert_admin import insert_admin
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from database.insert_data import insert_translations


# Charger les variables d'environnement
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Liste des fichiers SQL à exécuter dans l'ordre
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Chemin du dossier contenant run_migrations.py

MIGRATIONS = [
    os.path.join(BASE_DIR, '001_create_translations.sql'),
    os.path.join(BASE_DIR, '002_create_users_table.sql'),
    os.path.join(BASE_DIR, '003_add_unique_constraint.sql'),
    os.path.join(BASE_DIR, '004_add_timestamps_users.sql')
]

# Connexion à la base
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

try:
    # Exécuter chaque migration
    for migration_file in MIGRATIONS:
        with open(migration_file, 'r') as file:
            sql = file.read()
            cur.execute(sql)
            print(f"✅ Migration '{migration_file}' exécutée avec succès.")
    conn.commit()

    # Insertion des données
    insert_translations()
    insert_admin()

except Exception as e:
    conn.rollback()
    print("❌ Une erreur s'est produite :", e)

finally:
    cur.close()
    conn.close()
