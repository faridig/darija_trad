import psycopg2
import json

# Dictionnaire de mapping entre codes internes et ceux utilisés par NLLB
LANG_CODE_MAP = {
    "dr": "ary_Arab",  # darija
    "fr": "fra_Latn",  # français
    "en": "eng_Latn",  # anglais
    # ajoute ici d'autres si besoin
}

# Connexion à PostgreSQL
conn = psycopg2.connect(
    dbname="darija_db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Extraire toutes les paires source → cible
cur.execute("""
    SELECT source_lang, target_lang, source_text, target_text
    FROM translations
    WHERE source_text IS NOT NULL AND target_text IS NOT NULL
""")

rows = cur.fetchall()

# Fichier de sortie
with open("all_translations_dataset.json", "w", encoding="utf-8") as f:
    for src_lang, tgt_lang, src_text, tgt_text in rows:
        # Vérifie que les langues sont dans le mapping
        if src_lang in LANG_CODE_MAP and tgt_lang in LANG_CODE_MAP:
            data = {
                "translation": {
                    LANG_CODE_MAP[src_lang]: src_text,
                    LANG_CODE_MAP[tgt_lang]: tgt_text
                }
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

cur.close()
conn.close()
print("✅ Export terminé : all_translations_dataset.json")
