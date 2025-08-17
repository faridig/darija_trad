# Documentation Technique – Base de Données du Projet Darija

## 1. Présentation

Cette base de données PostgreSQL a été conçue pour stocker et gérer un corpus de paires de traductions multilingues, principalement entre le français/anglais et le darija marocain. Elle inclut également un système de gestion des utilisateurs pour une future exploitation via une API sécurisée.

Elle permet de :
- Stocker de manière persistante et structurée un large volume de traductions.
- Rechercher des traductions par direction linguistique (`fr` -> `dr`, etc.).
- Fournir une base de données solide pour un corpus d'entraînement de modèles NLP ou un outil éducatif.
- Gérer l'authentification des utilisateurs via des tokens JWT.

---

## 2. Dépendances Techniques

- **Base de Données** : PostgreSQL (version 13 ou supérieure)
- **Langage** : Python 3.9 ou supérieur
- **Bibliothèques Python Clés** :
  - `psycopg2-binary` : Connecteur PostgreSQL.
  - `SQLAlchemy` : ORM pour la modélisation et l'interaction avec la base.
  - `python-dotenv` : Gestion des variables d'environnement.
  - `passlib[bcrypt]` : Hachage des mots de passe.
  - `python-jose[cryptography]` : Gestion des tokens JWT.

---

## 3. Installation et Déploiement

### Installation Locale

L'installation est entièrement automatisée via un script shell.

1. **Cloner le dépôt** :
    ```bash
    git clone https://github.com/votre-utilisateur/darija_app_final.git
    cd darija_app_final
    ```

2. **Configurer le fichier `.env`** :  
   Copiez `.env.example` en `.env` et remplissez les variables, notamment `DB_NAME`, `DB_USER`, `DB_PASSWORD`, etc.

3. **Lancer le script d'installation** :  
   Ce script installe PostgreSQL, configure l'utilisateur et la base de données, et propose d'exécuter les migrations et le peuplement.
    ```bash
    bash database/install_postgresql.sh
    ```

### Déploiement vers Supabase

Une fois la base de données locale prête, vous pouvez la migrer vers une instance Supabase en production :
```bash
bash database/migrate_to_supabase.sh
```

---

## 4. Structure de la Base de Données

### Table `translations`  
Stocke les paires de traduction. Une contrainte d'unicité empêche les doublons exacts.

```sql
CREATE TABLE translations (
    id SERIAL PRIMARY KEY,
    source_lang VARCHAR(10),
    source_text TEXT,
    target_lang VARCHAR(10),
    target_text TEXT,
    CONSTRAINT unique_translation_pair UNIQUE (source_lang, source_text, target_lang, target_text)
);
```

### Table `users`  
Gère les informations des utilisateurs pour l'authentification.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login TIMESTAMPTZ
);
```

Les modèles conceptuels et physiques détaillés sont disponibles dans le dossier `database/models/`.

---

## 5. Choix Techniques

- **PostgreSQL** : Choisi pour sa robustesse, sa gestion native de l'UTF-8, ses fonctionnalités avancées (comme TIMESTAMPTZ pour les fuseaux horaires) et sa compatibilité avec l'écosystème Python.
- **Encodage UTF-8** : Obligatoire pour garantir le stockage et l'affichage corrects des caractères arabes et des accents.
- **SQLAlchemy** : Utilisé pour la modélisation objet (`models.py`) et la gestion des sessions, offrant une couche d'abstraction sécurisée et maintenable par-dessus les requêtes SQL brutes.
- **Fichier `.env`** : Pour une séparation claire entre la configuration (identifiants, clés secrètes) et le code, améliorant la sécurité et la portabilité.

---

## 6. Migrations

- Les évolutions du schéma de la base sont gérées par des scripts SQL numérotés dans le dossier `database/migrations/`.
- Chaque script est **idempotent**, ce qui signifie qu'il peut être exécuté plusieurs fois sans causer d'erreur.
- L'orchestration est assurée par le script Python `database/migrations/run_migrations.py`, qui garantit l'exécution dans le bon ordre.

---

## 7. Authentification

Le système d'authentification repose sur les standards suivants :
- **Hachage des mots de passe** : bcrypt via la bibliothèque `passlib`. Les mots de passe ne sont jamais stockés en clair.
- **Tokens** : JSON Web Tokens (JWT) signés avec l'algorithme HS256. Ils ont une durée de vie limitée pour plus de sécurité.
- **Flux** : Un utilisateur s'authentifie avec son nom d'utilisateur et son mot de passe pour obtenir un token d'accès, qu'il doit ensuite fournir dans l'en-tête `Authorization` pour accéder aux routes protégées.

---

# Registre des Traitements de Données Personnelles

Ce document constitue un registre des activités de traitement des données personnelles effectuées dans le cadre du projet Darija App, conformément au Règlement Général sur la Protection des Données (RGPD).

## 1. Identification du Responsable de Traitement

**Entité** : Projet Darija App  
**Contact** : [Votre Nom/Email de contact]

---

## 2. Description du Traitement

### Finalités du Traitement
Les données personnelles des utilisateurs sont collectées et traitées pour les finalités suivantes :
1. **Authentification et Gestion de Compte** : Permettre aux utilisateurs de créer un compte, de se connecter et d'accéder aux fonctionnalités de l'application.
2. **Sécurité** : Protéger l'application contre les accès non autorisés et les abus.
3. **Administration** : Permettre aux administrateurs de gérer l'application et les utilisateurs.

### Base Légale du Traitement
Le traitement est basé sur :
- **L'exécution d'un contrat** (Article 6.1.b du RGPD) : La création d'un compte par l'utilisateur constitue un contrat de service.
- **L'intérêt légitime** (Article 6.1.f du RGPD) : Pour assurer la sécurité du service.

---

## 3. Inventaire des Données Personnelles Traitées

Les données personnelles sont stockées dans la table `users` de la base de données.

| Table   | Champ            | Type de Donnée            | Description et Utilisation |
|:------- |:---------------- |:------------------------- |:---------------------------|
| `users` | `id`             | Identifiant Technique     | Identifiant unique généré par la base de données. |
| `users` | `username`       | Donnée d'Identification   | Nom d'utilisateur choisi par l'utilisateur pour se connecter. |
| `users` | `hashed_password`| Donnée d'Authentification | Mot de passe de l'utilisateur, stocké sous forme de hachage irréversible (bcrypt). |
| `users` | `is_admin`       | Donnée de Profil          | Flag booléen indiquant si l'utilisateur a des droits d'administrateur. |
| `users` | `created_at`     | Métadonnée                | Date et heure de création du compte utilisateur. |
| `users` | `last_login`     | Métadonnée                | Date et heure de la dernière connexion réussie de l'utilisateur. |

---

## 4. Durée de Conservation

- Les données des utilisateurs sont conservées tant que le compte de l'utilisateur est actif.
- En cas de suppression du compte par l'utilisateur ou après une période d'inactivité prolongée (ex: 3 ans), les données personnelles seront anonymisées ou supprimées de nos bases de données actives.

---

## 5. Destinataires des Données

Les données personnelles ne sont pas partagées avec des tiers. L'accès est strictement limité au personnel autorisé (administrateurs) pour des raisons de maintenance et de sécurité.
