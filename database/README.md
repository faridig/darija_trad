# 🗃️ Base de Données – Gestion de Traductions Multilingues avec Authentification

Ce module fournit une base de données PostgreSQL pour gérer un corpus de traductions multilingues (français, anglais, darija) avec un système d'authentification JWT et une interface de migration vers Supabase.

---

## 🧱 Structure du projet

database/
├── core/
│ ├── init.py
│ ├── db.py # Connexion à la base et session SQLAlchemy
│ ├── auth.py # Authentification JWT, gestion des tokens
│ ├── models.py # ORM des tables : User
├── models/
│ ├── mcd.txt # Modèle conceptuel de données
│ └── mpd.sql # Modèle physique de données
├── migrations/
│ ├── 001_create_translations.sql
│ ├── 002_create_users_table.sql
│ ├── 003_add_unique_constraint.sql
│ ├── 004_add_timestamps_users.sql
│ └── run_migrations.py
├── insert_admin.py # Ajout d’un compte admin
├── insert_data.py # Injection des traductions
├── queries.py # Requêtes SQL encapsulées (CRUD)
├── explore_translations.ipynb
├── install_postgresql.sh # Installation locale de PostgreSQL
└── migrate_to_supabase.sh # Export vers Supabase
└── requirements.txt

## 🔐 Authentification

Le système utilise FastAPI + JWT avec `passlib` et `python-jose` pour gérer :
- Hachage des mots de passe (`bcrypt`)
- Création et validation de tokens (`HS256`)
- Dépendance `verify_jwt_token` pour protéger les routes

### Exemple `.env` (⚠️ à personnaliser)

```env
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
DB_NAME=darija_db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET=your-secret-key
SUPABASE_URL=postgres://user:pass@host:port/db
PG_LOCAL_PASSWORD=yourpassword

## 🧪 Migrations SQL
Les migrations sont exécutées en Python via run_migrations.py, dans l'ordre défini :

Création de la table translations

Création de la table users

Ajout de contrainte UNIQUE (source_lang, source_text, ...)

Ajout des timestamps RGPD (created_at, last_login)

Les scripts sont idempotents ✅.

## 🧑‍💼 Utilisateur Admin
Créé automatiquement via :

python3 database/insert_admin.py
Ou exécuté en fin de run_migrations.py.

## 📊 Analyse & Exploration
Le fichier explore_translations.ipynb permet d’explorer la base :

Top langues traduites

Détection de doublons

Statistiques de volume

Exemples : 

SELECT COUNT(*) FROM translations;
SELECT * FROM translations LIMIT 10;

## Migration vers Supabase
Le script migrate_to_supabase.sh :

Exporte la base locale avec pg_dump

Importe dans Supabase via psql

Supprime les fichiers temporaires

📌 Assurez-vous d’avoir SUPABASE_URL dans .env.

## ⚙️ Installation PostgreSQL locale

bash database/install_postgresql.sh

Ce script :

Installe PostgreSQL via apt

Configure pg_hba.conf pour le mode md5

Crée la base, l’utilisateur

Propose l’exécution de run_migrations.py et la migration vers Supabase

## 📂 Modèle de Données

Table translations

Champ	                        Type	                        Description
id	                            SERIAL	                        Clé primaire
source_lang	                    VARCHAR(10)	                    Langue source (fr, en, dr)
source_text	                    TEXT	                        Texte à traduire
target_lang	                    VARCHAR(10)	                    Langue cible


Table users
Champ	                        Type	                        Description
id	                            SERIAL	                        Clé primaire
username	                    VARCHAR(50)	                    Identifiant unique
hashed_password	                TEXT	                        Mot de passe haché
is_admin	                    BOOLEAN	                        Utilisateur admin ?
created_at	                    TIMESTAMPTZ	                    Date de création
last_login	                    TIMESTAMPTZ	                    Dernière connexion


## ✅ Requêtes SQL disponibles
Les requêtes SQL sont encapsulées dans la classe TranslationQueries :

get_all (avec filtre sur langues)

get_by_id

create

update

delete

Toutes les requêtes sont journalisées avec temps d’exécution et erreurs.

## 📦 Dépendances

requirements.txt 

## 📌 Lancement rapide 

# Installation PostgreSQL locale
bash database/install_postgresql.sh

# Exécution des migrations (manuel)
python3 database/migrations/run_migrations.py

# Exploration
jupyter notebook database/explore_translations.ipynb


## 🛡️ Sécurité
JWT avec expiration configurable (ACCESS_TOKEN_EXPIRE_MINUTES)

Mots de passe hachés avec bcrypt

Contraintes UNIQUE SQL pour éviter les doublons

Migrations safe/idempotentes