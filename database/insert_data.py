import psycopg2
from dotenv import load_dotenv
import os
import sys
sys.path.append('../data')  # ajoute le chemin au dossier data
from normalise_data import load_translations_json, load_traductions_processed

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Charger les données
translations = load_translations_json("../data/darija_scrapping/translations.json")
processed = load_traductions_processed("../data/darija_sft_mixture/nettoyage/traductions_processed.json")
all_data = translations + processed

# Connexion à la base
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

# Requête d’insertion
insert_query = """
INSERT INTO translations (source_lang, source_text, target_lang, target_text)
VALUES (%s, %s, %s, %s);
"""

# Insertion en lot
for row in all_data:
    cur.execute(insert_query, (
        row["source_lang"],
        row["source_text"],
        row["target_lang"],
        row["target_text"]
    ))

conn.commit()
print(f"✅ {len(all_data)} traductions insérées avec succès.")

cur.close()
conn.close()
