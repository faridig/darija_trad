import json

def load_translations_json(filepath):
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
        return [{
            "source_lang": item["source_lang"],
            "source_text": item["source"],
            "target_lang": item["target_lang"],
            "target_text": item["target"]
        } for item in data["translations"]]


def load_traductions_processed(filepath):
    with open(filepath, encoding='utf-8') as f:
        raw = json.load(f)
    
    all_data = []
    for block in raw:
        src_lang, tgt_lang = block["direction"].split("_")
        for pair in block["pairs"]:
            all_data.append({
                "source_lang": src_lang,
                "source_text": pair["texte_cible"],
                "target_lang": tgt_lang,
                "target_text": pair["traduction"]
            })
    return all_data

# Exemple d’utilisation
if __name__ == "__main__":
    translations = load_translations_json("../data/darija_scrapping/translations.json")
    processed = load_traductions_processed("../data/darija_sft_mixture/nettoyage/traductions_processed.json")

    combined = translations + processed
    print(f"✅ Total traductions chargées : {len(combined)}")
    print("🔎 Exemple de donnée :", combined[0])

# Extraire les champs clés pour l'unicité
tuples = [
    (item["source_lang"], item["source_text"], item["target_lang"], item["target_text"])
    for item in combined
]

# Créer un set pour éliminer les doublons exacts
unique_translations = set(tuples)

print(f"🧮 Nombre total de traductions chargées : {len(combined)}")
print(f"🧹 Nombre de traductions uniques (nettoyées) : {len(unique_translations)}")
print(f"❌ Nombre de doublons exacts détectés : {len(combined) - len(unique_translations)}")


