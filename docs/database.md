# Documentation Technique – Base de données Darija App

## 1. Présentation

Cette base de données stocke des paires de traductions multilingues, principalement orientées vers le darija marocain, à partir du français, de l’anglais, et dans certains cas l’inverse.

Elle permet de :
- rechercher des traductions par direction linguistique
- filtrer par texte ou langue
- construire un corpus d’entraînement pour NLP ou un outil éducatif

---

## 2. Dépendances

- PostgreSQL (version 13 ou supérieure)
- Python 3.10 ou plus
- Bibliothèques Python nécessaires :
  - `psycopg2-binary`
  - `python-dotenv`
  - `pandas` (analyse dans Jupyter)
  - `sqlalchemy` (optionnelle)

---

## 3. Installation

### Étapes à suivre :

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/mon-utilisateur/darija_app_final.git
   cd darija_app_final


2. **Créer un environnement virtuel** :


python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

3. **Configurer le fichier .env** :

DB_NAME=darija_db
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432

4. **Créer la table et importer les données** :

python database/create_table.py
python database/insert_data.py


## 4. Structure de la base

La base contient une table unique appelée translations, avec les champs suivants :

CREATE TABLE translations (
    id SERIAL PRIMARY KEY,
    source_lang VARCHAR(10),
    source_text TEXT,
    target_lang VARCHAR(10),
    target_text TEXT
);

Voir les fichiers du modèle conceptuel et physique dans le dossier database/models/.

## 5. Choix techniques

PostgreSQL pour sa robustesse, sa gestion de l’UTF-8 et sa compatibilité avec les outils d’analyse

Type TEXT pour les champs textuels afin de ne pas limiter la taille des traductions

Encodage UTF-8 obligatoire pour garantir l'affichage correct de l’arabe et des caractères non latins

Structure simplifiée (table à plat) pour faciliter l’extraction et l’import des données

Utilisation d’un fichier .env pour séparer le code de la configuration

## 6. Migrations

Les scripts de création ou d’évolution de la base sont placés dans le dossier database/migrations/.

Ils permettent :

la création initiale de la table

l’ajout de colonnes ou de contraintes

la gestion de versions successives du modèle


## 7. Tests SQL

Des exemples de requêtes sont fournis dans le fichier :
tests/database/test_queries.sql

Chaque requête est précédée d’un commentaire indiquant :

l’objectif

les filtres ou jointures utilisés

les conditions appliquées

les optimisations éventuelles