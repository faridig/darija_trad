import json
import os
from collections import Counter
import re

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

# 🔹 Validation avancée du dataset
def run_data_checks(data):
    """
    Effectue une série de contrôles de qualité sur le jeu de données final.
    Cette version est adaptée pour les modèles multilingues (type NLLB)
    et ne considère pas les paires inversées (A->B et B->A) comme des doublons.
    """
    print("\n=== VALIDATION AVANCÉE DU DATASET ===")

    # 1️⃣ Champs obligatoires
    mandatory_fields = {"source_lang", "source_text", "target_lang", "target_text"}
    for i, d in enumerate(data):
        missing = mandatory_fields - d.keys()
        if missing:
            print(f"[ERREUR] Échantillon {i} : champs manquants : {missing}")

    # 2️⃣ Pas de textes identiques source/cible
    # Ceci reste un check utile pour détecter les erreurs de copie/coller.
    same = [d for d in data if d["source_text"].strip().lower() == d["target_text"].strip().lower()]
    if same:
        print(f"[WARNING] {len(same)} échantillon(s) ont un texte source identique au texte cible.")

    # 3️⃣ Caractères hors script pour chaque langue (anciennement 4️⃣)
    # Vérifie que le texte correspond bien à l'alphabet attendu pour la langue.
    regex_scripts = {
        "dr": re.compile(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9\s,\.\?!\'"()%-]+$'),
        "fr": re.compile(r'^[A-Za-zÀ-ÖØ-öø-ž0-9\s,\.\?!\'"()%-]+$'),
        "en": re.compile(r'^[A-Za-z0-9\s,\.\?!\'"()%-]+$')
    }
    invalid_chars_count = 0
    for i, d in enumerate(data):
        sl, tl = d["source_lang"], d["target_lang"]
        st, tt = d["source_text"], d["target_text"]
        
        # Vérification du texte source
        if sl in regex_scripts and not regex_scripts[sl].match(st):
            invalid_chars_count += 1
            if invalid_chars_count <= 5: # Affiche les 5 premiers exemples seulement pour ne pas polluer la sortie
                print(f"[WARNING] Ligne {i}, texte source ('{st[:30]}...') contient des caractères inattendus pour la langue '{sl}'")
        
        # Vérification du texte cible
        if tl in regex_scripts and not regex_scripts[tl].match(tt):
            invalid_chars_count += 1
            if invalid_chars_count <= 5:
                print(f"[WARNING] Ligne {i}, texte cible ('{tt[:30]}...') contient des caractères inattendus pour la langue '{tl}'")

    if invalid_chars_count > 5:
        print(f"[WARNING] ... et {invalid_chars_count - 5} autres avertissements de caractères non attendus.")

    # 4️⃣ Distribution des longueurs (anciennement 5️⃣)
    # Calcule les statistiques sur la longueur des phrases.
    if data: # Évite une erreur si la liste de données est vide
        lens = [len(d["source_text"].split()) for d in data] + [len(d["target_text"].split()) for d in data]
        if lens:
             print(f"[INFO] Statistiques de longueur (en mots) -> Min: {min(lens)}, Max: {max(lens)}, Moyenne: {sum(lens)//len(lens)}")
        else:
            print("[INFO] Aucune donnée textuelle à analyser pour la distribution des longueurs.")
    else:
        print("[INFO] Le jeu de données est vide.")


    print("=== FIN DES CHECKS ===\n")

# ... (le reste de votre fichier, y compris la section __main__, reste identique) ...

if __name__ == "__main__":
    # Cette partie reste inchangée et fonctionnera avec la fonction corrigée
    data = get_clean_data()
    if data:
        print("🔍 Exemple de traduction unique :")
        print(data[0])
        run_data_checks(data)
    else:
        print("Aucune donnée n'a été chargée.")