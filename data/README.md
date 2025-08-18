# 📊 Module `data` - Pipeline d'Acquisition et de Nettoyage de Données

Ce module est responsable de la construction du corpus de traduction. Il collecte, nettoie, normalise et valide les données à partir de deux sources distinctes pour garantir un dataset final riche et de haute qualité.

## 🏛️ Architecture du Pipeline de Données

Le pipeline est un processus en plusieurs étapes qui garantit la robustesse et la propreté des données :

1.  **Source A : Données Synthétiques & Scraping**
    *   `generer_questions.py` : Utilise l'API OpenAI (GPT-4o-mini) pour générer des phrases touristiques réalistes en français et en anglais.
    *   `scrapping.py` : Utilise **Playwright** pour automatiser un navigateur, se connecter au site `learnmoroccan.com` et traduire les phrases générées en Darija. Le résultat est stocké dans `translations.json`.

2.  **Source B : Dataset Public (Darija-SFT-Mixture)**
    *   `parquet_downloader.py` : Télécharge le dataset `MBZUAI-Paris/Darija-SFT-Mixture` depuis Hugging Face et le transfère directement sur **Azure Blob Storage**.
    *   `nettoyage_sft.py` : Utilise **PySpark** pour lire les fichiers Parquet depuis Azure. Il nettoie en profondeur le texte (suppression d'artefacts, normalisation) et extrait des paires de traduction structurées à partir des formats de conversation. Le résultat est stocké dans `traductions_processed.json`.

3.  **Étape Finale : Consolidation et Validation**
    *   `normalise_data.py` : Le cœur du module. Il fusionne les données des deux sources, normalise les codes de langue (ex: `darija` -> `dr`), supprime les doublons exacts et exécute une batterie de tests de qualité pour garantir la cohérence du dataset final.

## 📜 Description des Scripts

-   **`generer_questions.py`**
    -   **Rôle** : Créer un corpus source de haute qualité.
    -   **Entrée** : Aucune (génère de nouvelles données).
    -   **Sortie** : Fichiers Excel (`questions_fr_maroc.xlsx`, `questions_en_morocco.xlsx`).

-   **`scrapping.py`**
    -   **Rôle** : Traduire le corpus source en utilisant un site web externe.
    -   **Entrée** : Les fichiers Excel générés précédemment.
    -   **Sortie** : Un fichier `translations.json` contenant les paires de traduction.

-   **`parquet_downloader.py`**
    -   **Rôle** : Récupérer le dataset public et le stocker dans le cloud.
    -   **Entrée** : Identifiants Hugging Face et Azure.
    -   **Sortie** : Fichiers Parquet sur Azure Blob Storage.

-   **`nettoyage_csv.py`**
    -   **Rôle** : Traiter et nettoyer le dataset SFT.
    -   **Entrée** : Fichiers Parquet sur Azure.
    -   **Sortie** : `traductions_processed.json` (données valides) et `lignes_problematiques.csv` (erreurs).

-   **`normalise_data.py`**
    -   **Rôle** : Unifier, nettoyer et valider le corpus final.
    -   **Entrée** : `translations.json` et `traductions_processed.json`.
    -   **Sortie** : Une liste d'objets Python prête à être insérée en base de données.

## ⚙️ Prérequis et Installation

1.  **Dépendances Python** : Assurez-vous d'avoir installé les paquets listés dans le `requirements.txt` global. Les dépendances clés pour ce module sont :
    ```
    openai, pandas, playwright, azure-storage-blob, pyspark, huggingface_hub
    ```

2.  **Variables d'environnement** : Créez un fichier `.env` à la racine du projet avec les clés suivantes :
    ```env
    # Pour la génération de données
    OPENAI_API_KEY="sk-..."

    # Pour le téléchargement du dataset SFT
    HUGGINGFACE_TOKEN="hf_..."
    AZURE_STORAGE_ACCOUNT_NAME="..."
    AZURE_STORAGE_ACCOUNT_KEY="..."
    AZURE_CONTAINER_NAME="..."
    AZURE_STORAGE_CONNECTION_STRING="..."
    ```

3.  **Installation de Playwright** :
    ```bash
    playwright install
    ```

## 🚀 Mode d'Emploi

Pour exécuter le pipeline complet de ce module :

1.  **Générer les phrases sources :**
    ```bash
    python -m data.darija_scrapping.data_synthetique.generer_questions
    ```

2.  **Lancer le scraping pour les traduire :**
    ```bash
    python -m data.darija_scrapping.scrapping
    ```

3.  **Lancer le pipeline du dataset SFT (optionnel) :**
    ```bash
    # Étape 3a : Télécharger les données vers Azure
    python -m data.darija_sft_mixture.parquet_download.parquet_downloader

    # Étape 3b : Nettoyer les données avec Spark
    python -m data.darija_sft_mixture.nettoyage.nettoyage_sft
    ```

Le script `normalise_data.py` est conçu pour être appelé par le module `database` lors du peuplement, mais peut être exécuté manuellement pour inspection :
```bash
python -m data.normalise_data
```

## ✅ Sortie du Module

Le produit final de ce module est une structure de données Python (une liste de dictionnaires) nettoyée et validée, prête à être consommée par le module `database`. Chaque élément a la forme suivante :

```json
{
    "source_lang": "fr",
    "source_text": "Quel est le meilleur plat à essayer ici ?",
    "target_lang": "dr",
    "target_text": "شنو هو أحسن طبق نجرب هنا؟"
}
```
Les contrôles de qualité (`run_data_checks`) garantissent l'absence de champs manquants, de textes source/cible identiques et de caractères invalides pour chaque langue.