import os
import re
import json
import logging
import pandas as pd
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# ---------------------------------------------------------------------------
# Configuration du logging et chargement des variables d'environnement
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
load_dotenv()

storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
container_name = os.getenv("AZURE_CONTAINER_NAME")
parquet_folder = "data/"

if not storage_account_name or not storage_account_key or not container_name:
    raise ValueError("ERREUR : Variables d'environnement manquantes.")

# ---------------------------------------------------------------------------
# Configuration de Spark + dépendances
# ---------------------------------------------------------------------------

hadoop_jars_path = os.path.expanduser("~/hadoop_jars")
jars = [
    f"{hadoop_jars_path}/hadoop-azure-3.3.1.jar",
    f"{hadoop_jars_path}/azure-storage-8.6.6.jar",
    f"{hadoop_jars_path}/jetty-util-9.4.40.v20210413.jar",
    f"{hadoop_jars_path}/jetty-util-ajax-9.4.40.v20210413.jar"
]

spark = (
    SparkSession.builder
    .appName("AzureParquetAnalysis_Simplified")
    .master("local[*]")
    .config("spark.jars", ",".join(jars))
    .config("spark.hadoop.fs.azure", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
    .config(f"spark.hadoop.fs.azure.account.key.{storage_account_name}.blob.core.windows.net", storage_account_key)
    .config("spark.hadoop.fs.azure.account.auth.type", "SharedKey")
    .config("spark.sql.adaptive.enabled", "true")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .getOrCreate()
)

print("PySpark configuré avec les JAR Azure")

# ---------------------------------------------------------------------------
# Pattern pour supprimer « ترجم …: »
# ---------------------------------------------------------------------------

prefix_pattern = r"ترجم.*?:\s*"

# ---------------------------------------------------------------------------
# Fonction de nettoyage unifiée
# ---------------------------------------------------------------------------

def clean_text(text):
    """
    Nettoie TOUT texte (qu'il vienne de 'user' ou 'assistant') :

    1. Supprime le préfixe « ترجم …: » où qu'il soit dans la chaîne,
       par ex. "ترجم de la suite:Hello\\xa0world" => "Hello\\xa0world".
    2. Remplace la séquence littérale '\\xa0' par un espace,
       ex. "Hello\\xa0world" => "Hello world".
    3. Remplace également le vrai caractère insécable \xa0 (U+00A0) si présent,
       au cas où, pour le transformer en espace classique.

    Renvoie la chaîne nettoyée et trimée (strip).
    """
    # Supprime "ترجم ...:"
    text = re.sub(prefix_pattern, "", text)
    # Remplace la séquence littérale '\\xa0'
    text = text.replace("\\xa0", " ")
    # Remplace le caractère insécable \xa0
    # Remplace le vrai caractère U+00A0
    text = text.replace("\xa0", " ")
    # Remplace le caractère U+2009 (thin space)
    text = text.replace("\u2009", " ")
    # Corrige l’échappement supplémentaire des apostrophes 
    # "the world\\'s" => "the world's"
    text = text.replace("\\'", "'")
    # Remplace le backslash par un espace
    # "il a dit \ salut" => "il a dit   salut"
    text = text.replace("\\", " ")
    text = text.replace("\\/", "/")
    text = text.replace("\\", " ")      


    return text.strip()

# ---------------------------------------------------------------------------
# Fonctions d'extraction de paires
# ---------------------------------------------------------------------------

def split_conversation(convo):
    """
    Découpe un texte multi-tours avec "<|user|>" et "<|assistant|>"
    en une liste de paires { 'texte_cible': str, 'traduction': str }.

    EXEMPLE :
      convo = (
         "Il a récemment perdu un match...<|assistant|>"
         "راه خسر هاذ الايامات...<|user|>"
         "ترجم de la suite:Rejoindre un tel réseau...\\xa0<|assistant|>"
         "الانضمام لهاد الشبكة..."
      )

      => [
        {
          "texte_cible": "Il a récemment perdu un match...",
          "traduction": "راه خسر هاذ الايامات..."
        },
        {
          "texte_cible": "Rejoindre un tel réseau...",
          "traduction": "الانضمام لهاد الشبكة..."
        }
      ]

    ÉTAPES :
      1) Spliter au "<|user|>" (passage de parole à l'utilisateur).
      2) Pour chaque segment, couper au "<|assistant|>" (réponse).
      3) Nettoyer chaque partie (suppression 'ترجم...:', '\\xa0', etc.).
    """
    pairs = []
    segments = convo.split("<|user|>")
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        if "<|assistant|>" in segment:
            parts = segment.split("<|assistant|>")
            user_part = parts[0].strip()
            assistant_part = parts[1].strip() if len(parts) > 1 else ""
        else:
            user_part, assistant_part = segment, ""

        # Nettoyage unifié
        user_part = clean_text(user_part.replace("\\n", "").replace("<|assistant|>", "").replace("<|user|>", ""))
        assistant_part = clean_text(assistant_part.replace("\\n", "").replace("<|assistant|>", "").replace("<|user|>", ""))

        pairs.append({"texte_cible": user_part, "traduction": assistant_part})
    return pairs

def extract_pairs(row_str):
    """
    Transforme une chaîne de type Row(content='...', role='...') 
    en liste de paires { 'texte_cible': str, 'traduction': str }.

    1. On repère chaque Row(...) par regex pour extraire content et role.
    2. Si le premier user contient déjà des marqueurs <|assistant|> ou <|user|>,
       => on appelle split_conversation pour découper en plusieurs tours.
    3. Sinon, on alterne : user -> assistant -> user -> assistant...

    EXEMPLES :
      - "Row(content='Il a récemment perdu...', role='user'), Row(content='راه خسر...', role='assistant')"
        => [{"texte_cible": "Il a récemment perdu...", "traduction": "راه خسر..."}]

      - "Row(content='Il a récemment perdu...<|assistant|>راه خسر...', role='user')"
        => => on délègue à split_conversation(...) 
           => plusieurs paires si on a plusieurs tours dedans.
    """
    if not isinstance(row_str, str):
        logging.error("L'entrée n'est pas une chaîne de caractères.")
        return []

    # Repère tous les Row(...) par regex
    pattern = r"Row\(content=(?P<quote>['\"])(?P<content>.*?)(?P=quote),\s*role=['\"](?P<role>.*?)['\"]\)"
    matches = re.findall(pattern, row_str, re.DOTALL)
    if not matches:
        logging.warning("Aucun message trouvé.")
        return []

    first_role = matches[0][2]  # role du premier match
    first_text = matches[0][1]  # content du premier match

    # Si la première partie user contient <|assistant|> ou <|user|> => multi-tours
    if first_role == "user" and ("<|assistant|>" in first_text or "<|user|>" in first_text):
        pairs = split_conversation(first_text)
        # Recherche d'un éventuel assistant final hors du multi-tours
        external_assistant = ""
        for content, role in [(m[1], m[2]) for m in matches[::-1]]:
            if role == "assistant":
                external_assistant = clean_text(content.strip())
                break
        # Compléter la dernière traduction si vide
        if pairs and not pairs[-1]['traduction'] and external_assistant:
            pairs[-1]['traduction'] = external_assistant
        return pairs

    # Sinon, on fait une alternance user -> assistant
    msg_list = []
    for _, content, role in matches:
        # Nettoyage unifié
        clean_content = clean_text(content.replace("\\n", ""))
        msg_list.append({"role": role, "content": clean_content})

    pairs = []
    i = 0
    while i < len(msg_list):
        if msg_list[i]["role"] == "user":
            user_text = msg_list[i]["content"]
            assistant_text = ""
            if i + 1 < len(msg_list) and msg_list[i+1]["role"] == "assistant":
                assistant_text = msg_list[i+1]["content"]
            pairs.append({"texte_cible": user_text, "traduction": assistant_text})
            i += 2
        else:
            i += 1
    return pairs

def safe_extract(row):
    """
    Applique extract_pairs à la colonne 'messages' d'une ligne du DataFrame
    et complète la dernière traduction si on détecte un user sans assistant.

    EXEMPLE :
      row['messages'] = 
        "Row(content='Il a récemment perdu...', role='user'), 
         Row(content='راه خسر...', role='assistant')"
      => 
        [{"texte_cible": "Il a récemment perdu...", "traduction": "راه خسر..."}]

      Si on détecte un dernier user sans traduction, on tente d'ajouter row['traduction'].
    """
    pairs = extract_pairs(row['messages'])

    # Compte combien de <|user|> / <|assistant|> pour détecter un user en trop
    user_count = row['messages'].count("<|user|>") + 1
    assistant_count = row['messages'].count("<|assistant|>")

    # S'il y a un user de plus qu'assistant => on complète la dernière traduction
    if user_count - assistant_count == 1 and pairs:
        if not pairs[-1]['traduction']:
            pairs[-1]['traduction'] = clean_text(row.get("traduction", ""))
    return pairs

# ---------------------------------------------------------------------------
# Chargement des données brutes et sauvegarde en CSV
# ---------------------------------------------------------------------------

def load_raw_data():
    """
    1) Lit le Parquet depuis Azure
    2) Filtre sur certaines directions (en_dr, fr_dr, dr_fr, dr_en)
    3) Sauvegarde en CSV local
    4) Retourne le chemin vers ce CSV
    """
    directions = ["en_dr", "fr_dr", "dr_fr", "dr_en"]
    azure_url = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net/{parquet_folder}"
    logging.info(f"Lecture des Parquet depuis: {azure_url}")

    df = spark.read.parquet(azure_url).filter(col("direction").isin(directions))
    df_local = df.coalesce(4).toPandas()

    output_dir = "data_Darija-SFT-Mixture/darija_data"
    os.makedirs(output_dir, exist_ok=True)
    raw_file = os.path.join(output_dir, "donnees_brutes.csv")

    df_local.to_csv(raw_file, index=False)
    logging.info(f"Données brutes sauvegardées: {raw_file}")
    return raw_file

# ---------------------------------------------------------------------------
# Traitement final : extraction de paires, JSON de sortie et CSV d'erreurs
# ---------------------------------------------------------------------------

def process_csv(csv_file, output_json, error_csv):
    """
    1) Lit le CSV généré par load_raw_data()
    2) Extrait les paires via safe_extract => df['pairs']
    3) Marque les lignes sans paires => df['problem'] = True
    4) Sauvegarde les données valides en JSON (pairs + direction) 
       et les données problématiques en CSV.
    """
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        logging.exception("Erreur lecture CSV: %s", e)
        return

    df["pairs"] = df.apply(safe_extract, axis=1)
    df["problem"] = df["pairs"].apply(lambda x: not bool(x))  # True si liste vide

    df_valid = df[~df["problem"]].copy()
    df_problem = df[df["problem"]]

    df_valid["pair_count"] = df_valid["pairs"].apply(len)
    total_pairs = df_valid["pair_count"].sum()
    logging.info(f"Nombre total de paires extraites: {total_pairs}")

    # Écrit le JSON avec paires valides
    try:
        df_valid[["pairs", "direction"]].to_json(
            output_json, orient='records', force_ascii=False, indent=4
        )
        logging.info(f"JSON généré: {output_json}")
    except Exception as e:
        logging.exception("Erreur écriture JSON: %s", e)

    # Écrit un CSV séparé avec les lignes problématiques
    try:
        df_problem.to_csv(error_csv, index=False, encoding='utf-8')
        logging.info(f"CSV problématiques: {error_csv}")
    except Exception as e:
        logging.exception("Erreur écriture CSV problèmes: %s", e)

# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Démarrage du traitement...")
    csv_file = load_raw_data()

    output_dir = "data_Darija-SFT-Mixture/darija_data"
    output_json = os.path.join(output_dir, "traductions_processed.json")
    error_csv = os.path.join(output_dir, "lignes_problematiques.csv")

    process_csv(csv_file, output_json, error_csv)
    print("Traitement terminé")
    spark.stop()
