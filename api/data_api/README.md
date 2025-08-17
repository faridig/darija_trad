# 📡 Data API - Gestion du Corpus de Traduction Darija

Ce module contient l'API principale pour gérer le corpus de traduction. Construite avec **FastAPI**, elle permet les opérations CRUD sur les paires de traduction et gère l'authentification utilisateur via des tokens JWT.

Cette API est conçue pour être déployée dans un environnement conteneurisé, en utilisant Docker et Kubernetes (AKS).

## ✨ Fonctionnalités Clés

* **FastAPI** : Framework performant pour la construction d'APIs asynchrones.
* **Authentification JWT** : Système de gestion des utilisateurs sécurisé (inscription, connexion, tokens d'accès).
* **Gestion de la traduction** : Opérations CRUD complètes sur le corpus de traduction.
* **Intégration de la base de données** : Utilisation de **SQLAlchemy** pour interagir avec la base de données PostgreSQL (Supabase).
* **Déploiement Conteneurisé** : Utilisation de **Docker** pour la conteneurisation et **Azure Kubernetes Service (AKS)** pour l'orchestration.
* **Sécurité** : Hachage des mots de passe (`bcrypt`), gestion de `last_login` et Rate Limiting (`slowapi`).

## 🔑 Authentification

L'API utilise des tokens JWT pour sécuriser la plupart des routes.

1. **Inscription** : `POST /register`
2. **Connexion** : `POST /login`
3. **Accès aux données** : Token dans l'en-tête `Authorization` (`Bearer <token>`).

La connexion met à jour `last_login` pour la politique de conservation des données.

## 🗺️ Endpoints de l'API

### Authentification (`/auth`)

| Endpoint | Méthode | Description |
| :--- | :--- | :--- |
| `/auth/register` | `POST` | Crée un nouvel utilisateur. |
| `/auth/login` | `POST` | Authentifie et retourne un token JWT. |
| `/auth/me` | `GET` | Récupère les données de l'utilisateur connecté. |

### Traductions (`/translations`)

| Endpoint | Méthode | Description |
| :--- | :--- | :--- |
| `/translations` | `GET` | Liste les traductions (filtres possibles : `source_lang`, `target_lang`). |
| `/translations` | `POST` | Crée une nouvelle traduction. |
| `/translations/{id}` | `GET` | Récupère une traduction par ID. |
| `/translations/{id}` | `PUT` | Met à jour une traduction. |
| `/translations/{id}` | `DELETE` | Supprime une traduction. |

## 📦 Schémas de Données

Modèles Pydantic dans `schemas.py`.

**Langues supportées** : `fr`, `en`, `dr`

## 🚀 Déploiement

Prérequis :
* **Docker** installé.
* **Azure CLI** connecté.
* **kubectl** configuré.
* `.env` avec les variables nécessaires.

### 1. Build et Push

```bash
cd api/data_api/deploiement/
bash build_and_push_data_api.sh
```

### 2. Déploiement sur AKS

```bash
cd api/data_api/deploiement/
bash deploy_to_aks.sh
```

- Connexion à AKS.
- Création/mise à jour des secrets Kubernetes depuis `.env`.
- Mise à jour du manifeste `k8s/data-api.yaml` avec le nouveau tag.
- Lancement du déploiement.

## 🏗️ Architecture et Dépendances

- **`main.py`** : Point d'entrée FastAPI, configure CORS, Rate Limiting, routeurs.
- **`/routers`** : Routage pour `auth.py` et `translations.py`.
- **`Dockerfile`** : Définit l'environnement conteneurisé.
- **`database/`** : Connexion et requêtes SQL (voir README du module database).
