import psycopg2
from dotenv import load_dotenv
import os
import sys
from data.normalise_data import get_clean_data


load_dotenv()

def insert_translations():
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")

    unique_data = get_clean_data()

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    insert_query = """
    INSERT INTO translations (source_lang, source_text, target_lang, target_text)
    VALUES (%s, %s, %s, %s);
    """

    for row in unique_data:
        cur.execute(insert_query, (
            row["source_lang"],
            row["source_text"],
            row["target_lang"],
            row["target_text"]
        ))

    conn.commit()
    print(f"✅ {len(unique_data)} traductions insérées avec succès.")

    cur.close()
    conn.close()

# Pour l'exécuter en standalone
if __name__ == "__main__":
    insert_translations()
