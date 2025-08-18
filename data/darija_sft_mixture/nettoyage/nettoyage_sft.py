
"""
Ce script réalise le traitement ETL (Extract, Transform, Load) pour le dataset Darija-SFT-Mixture.
1.  EXTRACT : Lit les fichiers Parquet depuis un conteneur Azure Blob Storage.
2.  TRANSFORM : Filtre, nettoie, et restructure les données de conversation en paires de traduction propres.
3.  LOAD : Sauvegarde les données valides en JSON et les données problématiques en CSV pour analyse.
"""

# ==============================================================================
# 1. IMPORTATIONS ET CONFIGURATION INITIALE
# ==============================================================================
import os
import re
import json
import logging
import pandas as pd
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Configuration du logging pour afficher des messages clairs dans la console.
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Chargement des variables d'environnement (clés Azure) depuis le fichier .env.
load_dotenv()

# ==============================================================================
# 2. CONFIGURATION DE L'ACCÈS À AZURE
# ==============================================================================
storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
container_name = os.getenv("AZURE_CONTAINER_NAME")
parquet_folder = "data/" # Le sous-dossier contenant les fichiers Parquet dans le conteneur

# Vérification critique : le script ne peut pas fonctionner sans ces variables.
if not all([storage_account_name, storage_account_key, container_name]):
    raise ValueError("ERREUR : Variables d'environnement Azure manquantes dans le fichier .env.")

# ==============================================================================
# 3. INITIALISATION DE LA SESSION SPARK AVEC LES DÉPENDANCES AZURE
# ==============================================================================
# Chemin vers les drivers (JARs) nécessaires pour que Spark puisse communiquer avec Azure.
# Ces fichiers doivent être téléchargés manuellement au préalable.
hadoop_jars_path = os.path.expanduser("~/hadoop_jars")
jars = [
    f"{hadoop_jars_path}/hadoop-azure-3.3.1.jar",
    f"{hadoop_jars_path}/azure-storage-8.6.6.jar",
    f"{hadoop_jars_path}/jetty-util-9.4.40.v20210413.jar",
    f"{hadoop_jars_path}/jetty-util-ajax-9.4.40.v20210413.jar"
]

# Création de la session Spark. C'est le point d'entrée pour toute application Spark.
spark = (
    SparkSession.builder
    .appName("AzureParquetETL")
    .master("local[*]")  # Utilise tous les cœurs disponibles en local.
    .config("spark.jars", ",".join(jars))  # Fournit les drivers à Spark.
    # Configuration de l'authentification pour accéder à Azure Blob Storage.
    .config("spark.hadoop.fs.azure", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
    .config(f"spark.hadoop.fs.azure.account.key.{storage_account_name}.blob.core.windows.net", storage_account_key)
    .config("spark.hadoop.fs.azure.account.auth.type", "SharedKey")
    # Configurations d'optimisation.
    .config("spark.sql.adaptive.enabled", "true")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .getOrCreate()
)
logging.info("Session PySpark configurée avec succès pour l'accès à Azure.")

# ==============================================================================
# 4. FONCTIONS DE NETTOYAGE ET D'EXTRACTION DE DONNÉES
# ==============================================================================

# Expression régulière pour identifier et supprimer les préfixes de type "Traduire :" en arabe.
prefix_pattern = r"ترجم.*?:\s*"

def clean_text(text: str) -> str:
    """
    Fonction de nettoyage robuste pour une chaîne de caractères unique.
    Elle cible spécifiquement le "bruit" identifié dans le dataset.
    """
    if not isinstance(text, str):
        return ""
    # Enchaînement d'opérations de remplacement pour nettoyer le texte.
    text = re.sub(prefix_pattern, "", text) # Supprime le préfixe arabe
    text = text.replace("\\xa0", " ")      # Remplace l'espace insécable échappé
    text = text.replace("\xa0", " ")       # Remplace le vrai caractère espace insécable
    text = text.replace("\u2009", " ")     # Remplace l'espace fin
    text = text.replace("\\'", "'")        # Corrige les apostrophes doublement échappées
    text = text.replace("\\/", "/")
    text = text.replace("\\", " ")         # Remplace les backslashes restants
    return text.strip()                    # Supprime les espaces en début/fin de chaîne

def extract_pairs_from_row_string(row_str: str) -> list:
    """
    Fonction principale de parsing. Elle transforme une chaîne de caractères
    complexe représentant une conversation en une liste structurée de paires de traduction.
    Gère plusieurs formats de conversation trouvés dans le dataset.
    """
    if not isinstance(row_str, str):
        logging.warning("Entrée non-textuelle pour l'extraction de paires.")
        return []

    # Regex pour trouver toutes les occurrences de "Row(content='...', role='...')".
    pattern = r"Row\(content=(?P<quote>['\"])(?P<content>.*?)(?P=quote),\s*role=['\"](?P<role>.*?)['\"]\)"
    matches = re.findall(pattern, row_str, re.DOTALL)
    if not matches:
        return []

    # Le cœur de la logique : alterner entre 'user' et 'assistant' pour former des paires.
    pairs = []
    i = 0
    while i < len(matches):
        _, user_content, role = matches[i]
        if role == "user":
            assistant_content = ""
            if i + 1 < len(matches) and matches[i+1][2] == "assistant":
                assistant_content = matches[i+1][1]
                i += 1 # On avance de 2 si une paire est trouvée
            
            pairs.append({
                "texte_cible": clean_text(user_content),
                "traduction": clean_text(assistant_content)
            })
        i += 1
    return pairs

# ==============================================================================
# 5. ORCHESTRATION DU PIPELINE ETL
# ==============================================================================

def run_etl_pipeline():
    """
    Fonction principale qui orchestre les étapes d'extraction, transformation et chargement.
    """
    # --- 5.1. EXTRACT : Lire les données depuis Azure ---
    directions_to_keep = ["en_dr", "fr_dr", "dr_fr", "dr_en"]
    azure_url = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net/{parquet_folder}"
    logging.info(f"Lecture des fichiers Parquet depuis : {azure_url}")
    
    # Lecture des fichiers Parquet et conversion en DataFrame Pandas pour un traitement plus simple.
    df_spark = spark.read.parquet(azure_url).filter(col("direction").isin(directions_to_keep))
    df_pandas = df_spark.toPandas()
    logging.info(f"{len(df_pandas)} lignes chargées depuis Azure.")

    # --- 5.2. TRANSFORM : Appliquer le nettoyage et l'extraction ---
    logging.info("Application de la logique d'extraction et de nettoyage...")
    # Applique la fonction de parsing sur chaque ligne de la colonne 'messages'.
    df_pandas['extracted_pairs'] = df_pandas['messages'].apply(extract_pairs_from_row_string)
    
    # Marque les lignes qui n'ont pas pu être parsées.
    df_pandas['is_problematic'] = df_pandas['extracted_pairs'].apply(lambda x: not bool(x))
    
    # --- 5.3. LOAD : Séparer et sauvegarder les résultats ---
    df_valid = df_pandas[~df_pandas['is_problematic']].copy()
    df_problematic = df_pandas[df_pandas['is_problematic']]
    
    logging.info(f"{len(df_valid)} lignes valides et {len(df_problematic)} lignes problématiques trouvées.")
    
    output_dir = "data/darija_sft_mixture/nettoyage"
    os.makedirs(output_dir, exist_ok=True)
    
    # Sauvegarde des données valides au format JSON structuré.
    output_json_path = os.path.join(output_dir, "traductions_processed.json")
    valid_data_to_save = df_valid[['extracted_pairs', 'direction']].rename(columns={'extracted_pairs': 'pairs'})
    valid_data_to_save.to_json(output_json_path, orient='records', force_ascii=False, indent=4)
    logging.info(f"Données valides sauvegardées dans : {output_json_path}")
    
    # Sauvegarde des lignes problématiques pour une analyse manuelle.
    error_csv_path = os.path.join(output_dir, "lignes_problematiques.csv")
    df_problematic.to_csv(error_csv_path, index=False, encoding='utf-8')
    logging.info(f"Lignes problématiques sauvegardées dans : {error_csv_path}")

# ==============================================================================
# 6. POINT D'ENTRÉE DU SCRIPT
# ==============================================================================
if __name__ == "__main__":
    logging.info("Démarrage du pipeline ETL pour le dataset SFT...")
    try:
        run_etl_pipeline()
        logging.info("Pipeline ETL terminé avec succès.")
    except Exception as e:
        logging.error(f"Une erreur est survenue durant l'exécution du pipeline : {e}", exc_info=True)
    finally:
        # Il est crucial de toujours arrêter la session Spark pour libérer les ressources.
        spark.stop()
        logging.info("Session Spark arrêtée.")