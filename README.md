# Projet MLOps de Traduction Français/Anglais ↔ Darija Marocain

Ce projet met en œuvre un système de traduction de bout en bout basé sur le modèle NLLB-600M de Facebook, fine-tuné pour le darija marocain. Il implémente un cycle de vie MLOps complet, de la collecte des données au déploiement et au monitoring en production d'une API d'inférence, en passant par l'entraînement et la validation automatisés du modèle.

## ✨ Caractéristiques Principales

*   **🤖 Modèle d'IA :** Fine-tuning du modèle `facebook/nllb-200-distilled-600M` avec des adaptateurs LoRA pour une traduction performante et bidirectionnelle.
*   **🚀 Pipeline MLOps Automatisé :** Un workflow GitHub Actions gère l'entraînement, l'évaluation et le déploiement conditionnel du modèle sur Hugging Face Hub.
*   **✔️ Validation Gate :** Un nouveau modèle n'est déployé que si son score BLEU sur un jeu de test est supérieur à celui en production, garantissant une amélioration continue.
*   **📦 API d'Inférence Robuste :** Une API FastAPI conteneurisée expose le modèle via un endpoint sécurisé (JWT, headers de sécurité, rate limiting, validation Pydantic).
*   **📊 Monitoring Avancé :** Une stack complète Prometheus + Grafana surveille les performances de l'API, la latence et la dérive des données (*data drift*).
*   **⚙️ CI/CD pour l'Application :** Un second workflow GitHub Actions assure les tests, la construction et le déploiement des images Docker de l'API et de la stack de monitoring vers Azure Container Registry (ACR).
*   **🗃️ Gestion des Données Structurée :** Collecte de données multi-sources (scraping, synthétique via GPT, datasets publics), nettoyage avec PySpark, et gestion via une base de données PostgreSQL et une API CRUD dédiée.

## 🏛️ Architecture Globale

Le projet est divisé en deux boucles d'automatisation principales :

1.  **Le Cycle de Vie du Modèle (ML Pipeline) :** Dédié à la création, la validation et la publication du meilleur modèle possible.
2.  **Le Cycle de Vie de l'Application (CI/CD API) :** Dédié à la mise à disposition fiable et monitorée du modèle via une API.

```mermaid
graph TD
    subgraph "Phase 1: Gestion des Données (Compétences E1)"
        D1[Scraping Web] --> N
        D2[Génération Synthétique] --> N
        D3[Dataset Public HuggingFace] --> N
        N[Normalisation & Nettoyage] --> DB[(PostgreSQL)]
        DB <--> API_DATA[API CRUD Données]
    end

    subgraph "Phase 2: Pipeline MLOps - Entraînement (GitHub Actions - Runner GPU)"
        API_DATA -- Export --> PREP[Préparation Datasets]
        PREP --> TEST_DATA[Tests Qualité Données]
        TEST_DATA --> TRAIN[Fine-Tuning LoRA + MLflow]
        TRAIN --> EVAL[Évaluation Modèle (BLEU)]
        PROD_MODEL[Modèle en Prod (HF Hub)] --> COMPARE{Validation Gate}
        EVAL --> COMPARE
        COMPARE -- "Si score > prod" --> DEPLOY_MODEL[Déploiement sur Hugging Face Hub]
    end

    subgraph "Phase 3: Pipeline CI/CD - API (GitHub Actions)"
        CODE[Code de l'API IA] -- Push sur master --> TEST_API[Tests Pytest & Couverture > 85%]
        TEST_API --> BUILD[Build Images Docker]
        BUILD --> PUSH[Push vers Azure Container Registry]
    end
    
    subgraph "Phase 4: Déploiement Production (ex: Kubernetes)"
        DEPLOY_MODEL --> PULL_MODEL[API IA charge le modèle]
        PULL_MODEL <--> PROM[Prometheus]
        PROM <--> GRAFANA[Grafana Dashboard]
        PUSH --> K8S[Déploiement K8s]
        K8S --> PULL_MODEL
        USER[Utilisateur Final] --> PULL_MODEL
    end
```

## 📂 Structure du Projet

```
.
├── .github/workflows/      # Workflows CI/CD & MLOps
│   ├── ci-cd-ia-api.yml    # Pipeline pour l'API et le monitoring
│   └── ml_pipeline.yml     # Pipeline pour l'entraînement du modèle
├── api/
│   ├── data_api/           # API CRUD pour gérer le corpus de traductions
│   └── ia_api/             # API d'inférence pour le modèle de traduction
│       ├── grafana/        # Configuration Grafana (provisioning)
│       ├── prometheus/     # Configuration Prometheus
│       └── ...
├── data/                   # Scripts de collecte et nettoyage des données
├── database/               # Gestion de la BDD (modèles, migrations, scripts)
├── docs/                   # Documentation du projet (MLOps, BDD, etc.)
├── llm/                    # Scripts pour l'entraînement et l'évaluation du modèle
├── tests/                  # Tests automatisés
│   ├── api_crud/           # Tests pour l'API de données
│   ├── api_ia/             # Tests pour l'API d'IA (incluant test de charge)
│   ├── data/               # Tests de qualité des données
│   └── database/           # Tests des requêtes SQL
├── mlruns/                 # Données de tracking MLflow (local)
├── *.yaml                  # Fichiers de déploiement Kubernetes
├── requirements.txt        # Dépendances Python
└── README.md
```

## 🚀 Installation et Utilisation Locale

### Prérequis

*   Docker & Docker Compose
*   Python 3.11+
*   Un fichier `.env` à la racine du projet, configuré avec les secrets nécessaires (base de données, API keys, etc.).

### 1. Lancer l'API d'Inférence et le Monitoring

Depuis la racine du projet, le fichier `docker-compose.yml` est configuré pour lancer la stack de l'API IA.

```bash
# Dans le dossier api/ia_api/
docker-compose up --build -d
```

Les services suivants seront accessibles :
*   **API d'IA :** `http://localhost:8001`
*   **Documentation (Swagger) :** `http://localhost:8001/docs`
*   **Prometheus :** `http://localhost:9090`
*   **Grafana :** `http://localhost:3000` (login: `admin`/`admin`)

### 2. Exécuter les tests

Assurez-vous d'avoir installé les dépendances :
```bash
pip install -r requirements.txt
```

Lancez tous les tests avec la couverture :
```bash
pytest --cov
```

Pour lancer les tests d'un module spécifique (ex: API IA) :
```bash
pytest tests/api_ia/ --cov=api/ia_api
```

## ✅ Compétences Couvertes (Référentiel RNCP37827)

Ce projet a été conçu pour couvrir de manière exhaustive les blocs de compétences du titre "Développeur en Intelligence Artificielle".

| Bloc de Compétences                                      | Compétences Clés Démontrées                                                                                                                                                                                             | Fichiers de Preuve Principaux                                                                                                 |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **E1 : Gestion des données** <br/> (C1, C3, C4, C5)       | **C1:** Extraction multi-sources (scraping, API, datasets).<br/>**C3:** Agrégation et nettoyage avec PySpark.<br/>**C4:** Création d'une BDD PostgreSQL avec migrations.<br/>**C5:** Développement d'une API REST pour les données. | `data/`, `database/`, `api/data_api/`                                                                                         |
| **E3 : Mettre à disposition l’IA** <br/> (C9, C11, C12, C13) | **C9:** API d'inférence sécurisée avec FastAPI.<br/>**C11:** Monitoring complet (Prometheus/Grafana) avec détection de data drift.<br/>**C12:** Tests automatisés du modèle ("Validation Gate").<br/>**C13:** Chaînes CI/CD/MLOps complètes. | `api/ia_api/`, `.github/workflows/`, `llm/evaluate_model.py`, `tests/`                                                       |

Ce projet sert de démonstration pratique et approfondie des compétences requises pour l'industrialisation de solutions d'intelligence artificielle dans un environnement de production.