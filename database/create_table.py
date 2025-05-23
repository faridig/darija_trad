import psycopg2
from dotenv import load_dotenv
import os

# Charger les variables depuis le fichier .env
load_dotenv()

# Récupération des valeurs
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Connexion à PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

# Création d’un curseur pour exécuter des requêtes
cur = conn.cursor()

# Requête de création de la table
create_table_query = """
CREATE TABLE IF NOT EXISTS translations (
    id SERIAL PRIMARY KEY,
    source_lang VARCHAR(10),
    source_text TEXT,
    target_lang VARCHAR(10),
    target_text TEXT
);
"""

# Exécution et sauvegarde
cur.execute(create_table_query)
conn.commit()

print("✅ Table 'translations' créée avec succès.")

# Fermeture
cur.close()
conn.close()
