# Documentation Technique - E1 : Gestion des données

## 1. Vue d'ensemble
L'ensemble E1 concerne la gestion des données de traduction Darija ↔️ Français/Anglais. Cette documentation détaille l'extraction, le nettoyage et l'analyse des données du dataset MBZUAI-Paris/Darija-SFT-Mixture.

## 2. Source de données

### 2.1 Description
- **Source** : HuggingFace Datasets
- **URL** : https://huggingface.co/datasets/MBZUAI-Paris/Darija-SFT-Mixture
- **Format** : Parquet
- **Directions de traduction** :
  - Darija → Français (dr_fr)
  - Français → Darija (fr_dr)
  - Darija → Anglais (dr_en)
  - Anglais → Darija (en_dr)

### 2.2 Configuration
- Python 3.x
- Variables d'environnement :
  ```bash
  HUGGINGFACE_TOKEN=<votre_token_huggingface>
  AZURE_STORAGE_CONNECTION_STRING=<votre_chaine_connexion_azure>
  AZURE_CONTAINER_NAME=<nom_container_azure>
  AZURE_STORAGE_ACCOUNT_NAME=<nom_compte_stockage>
  AZURE_STORAGE_ACCOUNT_KEY=<clé_compte_stockage>
  ```
- Dépendances Python :
  ```bash
  pip install -r requirements.txt
  ```
- JAR Hadoop requis dans ~/hadoop_jars/

## 3. Traitement des Données

### 3.1 Pipeline de Nettoyage
1. Chargement depuis Azure
2. Filtrage des directions
3. Nettoyage du texte :
   - Suppression préfixes arabes
   - Normalisation espaces
   - Correction caractères
4. Extraction paires de traduction
5. Validation et export

### 3.2 Utilisation
```python
from data.darija_sft_mixture.nettoyage.nettoyage_csv import process_csv

# Les chemins seront créés automatiquement si nécessaire
process_csv(
    csv_file="data_Darija-SFT-Mixture/darija_data/donnees_brutes.csv",
    output_json="data_Darija-SFT-Mixture/darija_data/traductions_processed.json",
    error_csv="data_Darija-SFT-Mixture/darija_data/lignes_problematiques.csv"
)
```

### 3.3 Format des Données
```json
{
    "pairs": [
        {
            "texte_cible": "Texte source",
            "traduction": "Traduction darija"
        }
    ],
    "direction": "fr_dr"
}
```

## 4. Statistiques
```python
from data.darija_sft_mixture.statistics.dataset_statistics import DarijaStatsAPI
from pathlib import Path

api = DarijaStatsAPI(Path("."))
api.run()  # Génère dataset_stats.json dans le dossier courant
``` 