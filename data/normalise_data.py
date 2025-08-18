# Importe les bibliothèques nécessaires :
import json  
import os   
import re    

# --- CONFIGURATION INITIALE ---

# Détermine le chemin absolu du répertoire où se trouve ce script.
# C'est une pratique robuste pour s'assurer que les chemins vers les fichiers de données
# sont corrects, peu importe d'où le script est exécuté.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Dictionnaire utilisé pour standardiser les codes de langue.
# Permet de s'assurer que, peu importe comment la langue est écrite dans les fichiers sources
# (ex: "darija", "Darija"), elle sera toujours convertie en un code unique et court ("dr").
# C'est l'étape de NORMALISATION des données.
LANGUAGE_ALIAS = {
    "darija": "dr"
}

# Fonction utilitaire qui prend un code de langue en entrée
# et le retourne en version normalisée (minuscules et alias appliqué).
def normalize_lang(code):
    # .lower() convertit en minuscules. .get() cherche la clé dans le dictionnaire,
    # et si elle n'est pas trouvée, retourne la valeur par défaut (le code lui-même).
    return LANGUAGE_ALIAS.get(code.lower(), code.lower())

# --- CHARGEMENT DES SOURCES DE DONNÉES ---

# Fonction pour charger et transformer les données issues du scraping (translations.json).
def load_translations_json(filepath):
    with open(filepath, encoding='utf-8') as f: # Ouvre le fichier en spécifiant l'encodage UTF-8 (crucial pour les caractères arabes).
        data = json.load(f) # Charge le contenu JSON dans une structure Python.
        
        # C'est une étape de TRANSFORMATION (ETL: Extract, Transform, Load).
        # On parcourt chaque item de la liste "translations" dans le JSON.
        # Pour chaque item, on crée un nouveau dictionnaire avec une structure standardisée
        # (source_lang, source_text, target_lang, target_text).
        # Cela garantit que toutes les données, peu importe leur source, auront le même format.
        return [{
            "source_lang": normalize_lang(item["source_lang"]),
            "source_text": item["source"],
            "target_lang": normalize_lang(item["target_lang"]),
            "target_text": item["target"]
        } for item in data["translations"]]

# Fonction pour charger et transformer les données issues du traitement SFT (traductions_processed.json).
def load_traductions_processed(filepath):
    with open(filepath, encoding='utf-8') as f:
        raw = json.load(f)

    all_data = [] # On initialise une liste vide pour stocker les résultats.
    # Le fichier est une liste de "blocs", chaque bloc correspondant à une direction de traduction (ex: "fr_dr").
    for block in raw:
        # On extrait les langues à partir du champ "direction" en le coupant au niveau du "_".
        src_lang, tgt_lang = block["direction"].split("_")
        # On normalise immédiatement les codes de langue.
        src_lang = normalize_lang(src_lang)
        tgt_lang = normalize_lang(tgt_lang)

        # Chaque bloc contient une liste de "paires" de traduction.
        for pair in block["pairs"]:
            # On crée un dictionnaire avec la structure standard et on l'ajoute à notre liste.
            all_data.append({
                "source_lang": src_lang,
                "source_text": pair["texte_cible"],
                "target_lang": tgt_lang,
                "target_text": pair["traduction"]
            })
    return all_data

# --- FONCTION PRINCIPALE D'AGRÉGATION ---

# C'est la fonction principale qui orchestre le chargement, la fusion et le nettoyage.
def get_clean_data():
    # Construit les chemins complets et fiables vers les fichiers de données.
    translations_path = os.path.join(BASE_DIR, "darija_scrapping/translations.json")
    processed_path = os.path.join(BASE_DIR, "darija_sft_mixture/nettoyage/traductions_processed.json")

    # Appelle les fonctions de chargement pour récupérer les données des deux sources.
    translations = load_translations_json(translations_path)
    processed = load_traductions_processed(processed_path)

    # Étape de FUSION : combine les deux listes en une seule grande liste.
    combined = translations + processed
    print(f"📥 Données chargées (brutes) : {len(combined)} traductions")

    # Étape de DÉDOUBLONNAGE :
    seen = set() # Un 'set' est une structure de données très rapide pour vérifier l'existence d'un élément.
    unique_data = [] # La liste finale qui ne contiendra que des données uniques.

    for item in combined:
        # On crée une "clé" unique pour chaque traduction en combinant ses 4 champs.
        # Un tuple est utilisé car il est "hashable", c'est-à-dire qu'il peut être ajouté à un 'set'.
        key = (item["source_lang"], item["source_text"], item["target_lang"], item["target_text"])
        
        # Si la clé n'a jamais été vue auparavant...
        if key not in seen:
            seen.add(key) # ...on l'ajoute au 'set' pour se souvenir qu'on l'a vue.
            unique_data.append(item) # ...et on ajoute l'item à notre liste de données uniques.

    print(f"🧹 Traductions après nettoyage (uniques) : {len(unique_data)}")
    print(f"❌ Nombre de doublons éliminés : {len(combined) - len(unique_data)}")

    return unique_data

# --- VALIDATION AVANCÉE DE LA QUALITÉ DES DONNÉES ---

# Cette fonction agit comme un garde-fou final pour s'assurer de la qualité du dataset.
def run_data_checks(data):
    """
    Effectue une série de contrôles de qualité sur le jeu de données final.
    """
    print("\n=== VALIDATION AVANCÉE DU DATASET ===")

    # Test 1 : Vérifie qu'aucun champ essentiel n'est manquant ou vide.
    mandatory_fields = {"source_lang", "source_text", "target_lang", "target_text"}
    for i, d in enumerate(data):
        missing = mandatory_fields - d.keys() # Trouve les clés manquantes.
        if missing:
            print(f"[ERREUR] Échantillon {i} : champs manquants : {missing}")

    # Test 2 : Détecte les anomalies où le texte source est identique au texte cible.
    same = [d for d in data if d["source_text"].strip().lower() == d["target_text"].strip().lower()]
    if same:
        print(f"[WARNING] {len(same)} échantillon(s) ont un texte source identique au texte cible.")

    # Test 3 : Vérifie que le script (alphabet) du texte correspond à la langue déclarée.
    # C'est crucial pour l'entraînement du modèle.
    regex_scripts = {
        # Accepte les lettres arabes, chiffres, et ponctuation courante.
        "dr": re.compile(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9\s,\.\?!\'"()%-]+$'),
        # Accepte les lettres latines (y compris accentuées), chiffres, et ponctuation.
        "fr": re.compile(r'^[A-Za-zÀ-ÖØ-öø-ž0-9\s,\.\?!\'"()%-]+$'),
        # Accepte les lettres latines (sans accents), chiffres, et ponctuation.
        "en": re.compile(r'^[A-Za-z0-9\s,\.\?!\'"()%-]+$')
    }
    invalid_chars_count = 0
    for i, d in enumerate(data):
        sl, tl = d["source_lang"], d["target_lang"]
        st, tt = d["source_text"], d["target_text"]
        
        # Si le code langue est dans notre dictionnaire de regex ET que le texte ne correspond PAS au pattern...
        if sl in regex_scripts and not regex_scripts[sl].match(st):
            invalid_chars_count += 1
            # On n'affiche que les 5 premiers pour ne pas polluer la console.
            if invalid_chars_count <= 5: 
                print(f"[WARNING] Ligne {i}, texte source ('{st[:30]}...') contient des caractères inattendus pour la langue '{sl}'")
        
        # Même vérification pour le texte cible.
        if tl in regex_scripts and not regex_scripts[tl].match(tt):
            invalid_chars_count += 1
            if invalid_chars_count <= 5:
                print(f"[WARNING] Ligne {i}, texte cible ('{tt[:30]}...') contient des caractères inattendus pour la langue '{tl}'")

    if invalid_chars_count > 5:
        print(f"[WARNING] ... et {invalid_chars_count - 5} autres avertissements de caractères non attendus.")

    # Test 4 : Calcule des statistiques sur la longueur des textes (en nombre de mots).
    # Utile pour repérer des phrases anormalement longues ou courtes.
    if data:
        lens = [len(d["source_text"].split()) for d in data] + [len(d["target_text"].split()) for d in data]
        if lens:
             print(f"[INFO] Statistiques de longueur (en mots) -> Min: {min(lens)}, Max: {max(lens)}, Moyenne: {sum(lens)//len(lens)}")
        else:
            print("[INFO] Aucune donnée textuelle à analyser.")
    else:
        print("[INFO] Le jeu de données est vide.")

    print("=== FIN DES CHECKS ===\n")

# --- POINT D'ENTRÉE DU SCRIPT ---
# Ce bloc de code ne s'exécute que si on lance ce fichier directement (ex: `python normalise_data.py`).
# Il ne s'exécute pas si ce fichier est importé par un autre script.
if __name__ == "__main__":
    data = get_clean_data() # Appelle la fonction principale.
    if data:
        print("🔍 Exemple de traduction unique :")
        print(data[0]) # Affiche le premier élément pour vérification.
        run_data_checks(data) # Lance la validation finale.
    else:
        print("Aucune donnée n'a été chargée.")