# Chaîne de Livraison Continue (CI/CD) pour le Modèle de Traduction

Ce document décrit la chaîne de CI/CD MLOps mise en place pour automatiser la validation, l'entraînement, et le packaging du modèle de traduction NLLB-LoRA.

## 1. Vue d'ensemble

La chaîne de CI/CD est définie dans le fichier `.github/workflows/ml_pipeline.yml` et utilise [GitHub Actions](https://docs.github.com/en/actions). Elle est conçue pour s'exécuter sur un **self-hosted runner** local et assure la traçabilité des expériences avec un **serveur MLflow**.

Le pipeline est composé d'un job principal : `validate-and-train`.

## 2. Déclencheurs (Triggers)

Le workflow est déclenché automatiquement dans les cas suivants :

1.  **Push sur la branche `main`** : Uniquement si des fichiers spécifiques sont modifiés :
    *   `llm/all_translations_dataset.json` (mise à jour des données d'entraînement)
    *   `llm/finetune_nllb_lora.py` (modification du script d'entraînement)
    *   `.github/workflows/ml_pipeline.yml` (modification de la chaîne elle-même)
2.  **Manuel (`workflow_dispatch`)** : Le workflow peut être lancé manuellement à tout moment depuis l'onglet "Actions" du dépôt GitHub.

## 3. Étapes du Job `validate-and-train`

Le job exécute les tâches suivantes en séquence :

| Étape                                   | Commande exécutée                    | Description                                                                                             |
| --------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| 1. Checkout du code                     | `actions/checkout@v4`                | Récupère la dernière version du code depuis le dépôt Git.                                               |
| 2. Configuration de Python              | `actions/setup-python@v5`            | Installe et configure l'environnement Python 3.11 sur le runner.                                        |
| 3. Installation des dépendances         | `pip install -r requirements.txt`    | Installe toutes les bibliothèques Python nécessaires au projet.                                         |
| 4. Validation des données               | `pytest tests/data/test_data_quality.py` | Exécute les tests de qualité sur les données. **La chaîne s'arrête si un test échoue.**                   |
| 5. Entraînement & Validation du modèle  | `python llm/finetune_nllb_lora.py`   | Lance le script de fine-tuning. Ce script entraîne le modèle, le valide (score BLEU) et logue tout dans MLflow. |
| 6. Sauvegarde de l'artefact             | `actions/upload-artifact@v4`         | "Package" le modèle entraîné (dossier `nllb-darija-lora-model`) en tant qu'artefact sur GitHub Actions.   |

## 4. Prérequis et Configuration

Pour exécuter cette chaîne, un environnement local doit être configuré.

### a. Configuration du Self-Hosted Runner

Un runner local est nécessaire pour exécuter le job. Il doit être configuré avec les étiquettes (`labels`) suivantes : `self-hosted, linux, x64, gpu`.

**Procédure d'installation :**
1.  Naviguez vers `Settings > Actions > Runners` sur le dépôt GitHub.
2.  Cliquez sur "New self-hosted runner" et choisissez "Linux".
3.  Suivez les instructions de téléchargement et de configuration fournies. Lors de la configuration, assignez les étiquettes mentionnées ci-dessus.
4.  Lancez le runner dans un terminal avec la commande `./run.sh`. **Ce terminal doit rester ouvert.**

### b. Configuration du Serveur MLflow

La traçabilité des expériences est gérée par un serveur MLflow local.

**Procédure de lancement :**
1.  Ouvrez un second terminal.
2.  Installez MLflow si ce n'est pas déjà fait : `pip install mlflow`.
3.  Créez les dossiers de stockage :
    ```bash
    mkdir -p ~/mlflow-tracking/{mlflow-backend-store,mlflow-artifacts}
    ```
4.  Lancez le serveur :
    ```bash
    mlflow server \
        --backend-store-uri ~/mlflow-tracking/mlflow-backend-store \
        --default-artifact-root ~/mlflow-tracking/mlflow-artifacts \
        --host 0.0.0.0 --port 5001
    ```
5.  L'interface de MLflow est accessible via un navigateur à l'adresse `http://localhost:5001`.

## 5. Comment tester la chaîne

1.  Assurez-vous que le self-hosted runner et le serveur MLflow sont en cours d'exécution localement (dans deux terminaux distincts).
2.  Faites une modification sur l'un des fichiers suivis (par exemple, ajoutez un commentaire dans `llm/finetune_nllb_lora.py`).
3.  Commitez et poussez la modification vers la branche `main`.
    ```bash
    git add .
    git commit -m "Test: déclenchement de la chaîne CI/CD"
    git push origin main
    ```
4.  Allez dans l'onglet "Actions" de votre dépôt GitHub pour suivre l'exécution du workflow en temps réel.
5.  Consultez l'interface MLflow (`http://localhost:5001`) pour voir la nouvelle "run" apparaître avec ses métriques et artefacts.