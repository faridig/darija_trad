import json
import os

# Base du chemin absolu, où se trouve ce fichier
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 🔹 Dictionnaire de normalisation des langues
LANGUAGE_ALIAS = {
    "darija": "dr"
   
}

# 🔹 Fonction pour normaliser les codes de langue
def normalize_lang(code):
    return LANGUAGE_ALIAS.get(code.lower(), code.lower())

# 🔹 Fonction pour charger un fichier JSON au format brut (scraping)
def load_translations_json(filepath):
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
        # On reformate les champs pour normaliser la structure
        return [{
            "source_lang": normalize_lang(item["source_lang"]),
            "source_text": item["source"],
            "target_lang": normalize_lang(item["target_lang"]),
            "target_text": item["target"]
        } for item in data["translations"]]

# 🔹 Fonction pour charger les traductions prétraitées (structurées en blocs)
def load_traductions_processed(filepath):
    with open(filepath, encoding='utf-8') as f:
        raw = json.load(f)
    
    all_data = []
    for block in raw:
        # On extrait les langues source et cible à partir du champ "direction"
        src_lang, tgt_lang = block["direction"].split("_")
        src_lang = normalize_lang(src_lang)
        tgt_lang = normalize_lang(tgt_lang)

        for pair in block["pairs"]:
            all_data.append({
                "source_lang": src_lang,
                "source_text": pair["texte_cible"],
                "target_lang": tgt_lang,
                "target_text": pair["traduction"]
            })
    return all_data

# 🔹 Fonction principale pour charger et nettoyer les données
def get_clean_data():
    # Construire les chemins absolus
    translations_path = os.path.join(BASE_DIR, "darija_scrapping/translations.json")
    processed_path = os.path.join(BASE_DIR, "darija_sft_mixture/nettoyage/traductions_processed.json")

    # Charger les deux sources de données
    translations = load_translations_json(translations_path)
    processed = load_traductions_processed(processed_path)
    
    # Combinaison des deux jeux de données
    combined = translations + processed
    print(f"📥 Données chargées (brutes) : {len(combined)} traductions")

    # Nettoyage des doublons exacts
    seen = set()
    unique_data = []

    for item in combined:
        key = (item["source_lang"], item["source_text"], item["target_lang"], item["target_text"])
        if key not in seen:
            seen.add(key)
            unique_data.append(item)

    print(f"🧹 Traductions après nettoyage (uniques) : {len(unique_data)}")
    print(f"❌ Nombre de doublons éliminés : {len(combined) - len(unique_data)}")

    return unique_data

# 🔹 Test local si exécuté directement
if __name__ == "__main__":
    data = get_clean_data()
    print("🔍 Exemple de traduction unique :")
    print(data[0])
