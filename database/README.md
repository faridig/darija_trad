# 🗃️ Module `database` - Gestion de la Base de Données et Authentification

Ce module gère le stockage persistant du corpus de traduction dans une base de données **PostgreSQL**. Il inclut un système de migration, le peuplement des données, un modèle d'authentification utilisateur basé sur **JWT**, des scripts de maintenance, et des utilitaires pour l'installation locale et le déploiement sur **Supabase**.

## 🧱 Structure du Module

- **`/core`**: Le cœur logique de l'application.
    - `db.py`: Configure la connexion à la base de données avec **SQLAlchemy** et gère les sessions. Gère intelligemment les environnements local et de production (`Supabase`).
    - `auth.py`: Implémente la logique d'authentification, incluant le hachage de mot de passe (`bcrypt`), la création et la validation de tokens **JWT**.
    - `models.py`: Définit les modèles ORM (`User`) avec SQLAlchemy.
- **`/maintenance`**: Contient les scripts pour les tâches de maintenance récurrentes.
    - `cleanup_inactive_users.py`: Supprime les comptes utilisateurs inactifs conformément à la politique de conservation des données.
    - `run_cleanup_task.sh`: Script lanceur pour l'automatisation via des planificateurs de tâches (ex: cron, Planificateur de tâches Windows).
- **`/migrations`**: Contient les scripts SQL pour faire évoluer le schéma de la base.
    - `00X_...sql`: Fichiers de migration numérotés, écrits pour être **idempotents**.
    - `run_migrations.py`: Orchestrateur Python qui exécute les migrations dans l'ordre, puis lance le peuplement des données et la création de l'admin.
- **`insert_data.py`**: Script qui importe les données nettoyées depuis le module `data` et les insère dans la table `translations`.
- **`insert_admin.py`**: Crée un utilisateur administrateur initial à partir des variables d'environnement.
- **`queries.py`**: Une classe `TranslationQueries` qui encapsule des requêtes SQL optimisées pour les opérations CRUD sur les traductions.
- **`install_postgresql.sh`**: Script d'automatisation pour installer et configurer PostgreSQL en local.
- **`migrate_to_supabase.sh`**: Script pour exporter la base locale et l'importer dans une instance Supabase.

## 📝 Modèle de Données

### Table `translations`
| Champ | Type | Description |
| :--- | :--- | :--- |
| `id` | SERIAL | Clé primaire auto-incrémentée |
| `source_lang` | VARCHAR(10) | Code de la langue source (ex: 'fr', 'en', 'dr') |
| `source_text` | TEXT | Texte original |
| `target_lang` | VARCHAR(10) | Code de la langue cible |
| `target_text` | TEXT | Texte traduit |
| **Contrainte** | UNIQUE | `(source_lang, source_text, target_lang, target_text)` |

### Table `users`
| Champ | Type | Description |
| :--- | :--- | :--- |
| `id` | SERIAL | Clé primaire auto-incrémentée |
| `username` | VARCHAR(50) | Nom d'utilisateur (unique) |
| `hashed_password` | TEXT | Mot de passe haché avec bcrypt |
| `is_admin` | BOOLEAN | Statut administrateur |
| `created_at` | TIMESTAMPTZ | Date de création du compte (conforme RGPD) |
| `last_login` | TIMESTAMPTZ | Date de la dernière connexion (utilisé pour la politique de conservation des données) |

## ⚙️ Installation et Configuration Locale

1. **Prérequis** : PostgreSQL doit être accessible sur votre système.

2. **Variables d'environnement** : Assurez-vous que votre fichier `.env` contient :
    ```env
    DB_USER=votre_user
    DB_PASSWORD=votre_mot_de_passe
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=darija_db
    PG_LOCAL_PASSWORD=votre_mot_de_passe_postgres_system
    ADMIN_USERNAME=admin
    ADMIN_PASSWORD=admin_password
    JWT_SECRET=une_cle_secrete_tres_longue_et_aleatoire
    SUPABASE_URL="postgres://..."
    ```

3. **Lancer le script d'installation** :
    ```bash
    bash database/install_postgresql.sh
    ```

## 🔄 Migrations et Peuplement

```bash
python -m database.migrations.run_migrations
```
Ce script :
1. Exécute les migrations SQL depuis `/migrations`.
2. Appelle `insert_data.py`.
3. Appelle `insert_admin.py`.

## 🧹 Maintenance et Automatisation

### Suppression des Utilisateurs Inactifs
- **Script** : `database/maintenance/cleanup_inactive_users.py`
- Supprime les comptes inactifs depuis plus de 3 ans.
- Protège le compte admin.

**Exécution manuelle** :
```bash
python -m database.maintenance.cleanup_inactive_users
```

Automatisation : via `run_cleanup_task.sh` (cron, Planificateur de tâches).

## 🚀 Migration vers Supabase

```bash
bash database/migrate_to_supabase.sh
```

## 🔐 Utilisation (Requêtes et Authentification)

```python
from database.core.db import get_db
from database.queries import TranslationQueries

db = next(get_db())
all_translations = TranslationQueries.get_all(db, source_lang='fr')
```

```python
from fastapi import Depends
from database.core.auth import verify_jwt_token

@app.get("/protected")
def protected_route(current_user: dict = Depends(verify_jwt_token)):
    return {"message": "Welcome!", "user": current_user}
```
