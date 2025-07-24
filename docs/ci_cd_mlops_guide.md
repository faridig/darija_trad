```markdown
# Guide de la Chaîne de Livraison Continue (CI/CD) et Approche MLOps du Modèle NLLB-LoRA Darija

Ce document décrit l'implémentation de la chaîne de livraison continue (CI/CD) et l'approche MLOps adoptées pour le modèle de traduction **NLLB-LoRA Darija** et son API d'exposition. Il vise à détailler les processus automatisés de tests, d'entraînement, de validation, de packaging et de déploiement, en lien avec les compétences **E3** du référentiel.

---

## 1. Introduction et Principes MLOps

Ce projet intègre les principes du **MLOps** (Machine Learning Operations) pour industrialiser le cycle de vie du modèle d'Intelligence Artificielle. Notre approche vise à garantir la **reproductibilité**, la **fiabilité**, l'**automatisation** et le **suivi** des modèles en production.

Les objectifs clés de notre chaîne CI/CD/MLOps sont :

* **Intégration Continue (CI)** : Assurer la qualité du code de l'API et du modèle via des tests automatisés à chaque modification.
* **Livraison Continue (CD)** : Automatiser le packaging et le déploiement de l'API et des nouvelles versions du modèle validées.
* **Validation Continue du Modèle** : Mettre en place une "validation gate" pour s'assurer que seules les versions de modèle performantes sont déployées.
* **Monitoring en Production** : Surveiller le comportement de l'API et du modèle pour détecter les anomalies et informer les décisions de réentraînement.

---

## 2. Les Pipelines CI/CD

Nous utilisons **GitHub Actions** pour orchestrer nos pipelines d'intégration et de livraison continues. Deux workflows principaux sont définis :

### 2.1. Pipeline CI/CD pour l'API et le Monitoring (`.github/workflows/ci-cd-ia-api.yml`)

Ce pipeline est dédié à la qualité et au déploiement de l'API de traduction et de son infrastructure de monitoring.

* **Déclencheurs :**
    * `on: push` sur la branche `master` si les chemins `api/ia_api/**`, `database/**` ou le workflow lui-même (`.github/workflows/ci-cd-ia-api.yml`) sont modifiés.
    * `on: pull_request` vers `master` pour les mêmes chemins.
    * `workflow_dispatch` pour un déclenchement manuel via l'interface GitHub.
* **Jobs et Étapes :**
    1.  **`test-api` (Intégration Continue)**
        * **Objectif :** Valider la qualité du code de l'API et des modules de base de données.
        * **Exécution sur :** `ubuntu-latest`.
        * **Étapes clés :**
            * `Checkout du code`
            * `Setup Python 3.11`
            * `Installer les dépendances`
            * `Lancer les tests de l'API IA`
    2.  **`build-and-deploy-images` (Déploiement Continu)**
        * **Objectif :** Construire les images Docker de l'API, Prometheus et Grafana, puis les pousser vers Azure Container Registry (ACR).
        * **Conditions :** Ne s'exécute que si le job `test-api` réussit ET sur un `push` vers la branche `master`.
        * **Exécution sur :** `ubuntu-latest`.
        * **Étapes clés :**
            * `Checkout du code`
            * `Connexion à Azure Container Registry (ACR)`
            * `Build and Push IA API Image`
            * `Build and Push Prometheus Image`
            * `Build and Push Grafana Image`

* **Lien avec les compétences E3 :**
    * **C9 (API)**
    * **C11 (Monitoring)**
    * **C13 (CI/CD)**

### 2.2. Pipeline MLOps pour l'Entraînement et le Déploiement du Modèle (`.github/workflows/ml_pipeline.yml`)

Ce pipeline gère l'ensemble du cycle de vie du modèle d'apprentissage automatique, de l'entraînement à la validation et au déploiement conditionnel.

* **Déclencheurs :**
    * `on: push` sur la branche `master` si les chemins `llm/**`, `tests/data/**` ou le workflow lui-même sont modifiés.
    * `workflow_dispatch` pour un déclenchement manuel.
* **Environnement d'exécution :** Utilise un `self-hosted, linux, x64, gpu` runner.
* **Jobs et Étapes :**
    1.  **`train-and-validate` (Entraînement et Pré-validation)**
        * **Objectif :** Entraîner le modèle NLLB-LoRA, effectuer des tests de qualité de données et sauvegarder les artefacts.
        * **Environnement :** `training`.
        * **Étapes clés :**
            * `Checkout du code`
            * `Restaurer les checkpoints depuis le cache`
            * `Setup Python 3.11` et `Installer les dépendances`
            * `Récupérer le corpus de données complet via l'API`
            * `Préparer et diviser les datasets`
            * `Lancer les tests de qualité sur les données`
            * `Lancer le Fine-Tuning du modèle avec MLflow`
            * `Sauvegarder les checkpoints dans le cache`
            * `Sauvegarder l'artefact du modèle LoRA`
            * `Sauvegarder l'artefact du jeu de test`
            * `Nettoyer les anciens caches`
    2.  **`validate-and-compare` (Validation et Comparaison du Modèle - "Validation Gate")**
        * **Objectif :** Évaluer le nouveau modèle entraîné et le comparer au modèle actuellement en production.
        * **Conditions :** Dépend du succès du job `train-and-validate`.
        * **Exécution sur :** `self-hosted, linux, x64, gpu` runner.
        * **Étapes clés :**
            * `Télécharger l'artefact du nouveau modèle` et `Télécharger l'artefact du jeu de test`
            * `Évaluer le NOUVEAU modèle sur le jeu de test`
            * `Récupérer le score du modèle en PRODUCTION`
            * `Comparer les scores`
    3.  **`deploy-model-to-hub` (Déploiement Conditionnel)**
        * **Objectif :** Déployer le nouveau modèle sur Hugging Face Hub si sa performance est jugée supérieure.
        * **Conditions :** Dépend du succès du job `validate-and-compare` ET si l'output `is_better` est `true`.
        * **Exécution sur :** `ubuntu-latest`.
        * **Étapes clés :**
            * `Télécharger l'artefact du modèle`
            * `Créer le fichier d'évaluation`
            * `Installer Git LFS et Hugging Face Hub CLI`
            * `Push vers Hugging Face Hub (Modèle + Score)`

* **Lien avec les compétences E3 :**
    * **C12 (Tests Automatisés du Modèle)**
    * **C13 (Chaîne de Livraison Continue)**

---

## 3. Stratégie de Monitoring (C11)

Le monitoring de l'API et du modèle est une pierre angulaire de notre approche MLOps.

### 3.1. Métriques Collectées

Les métriques sont exposées via l'endpoint `/metrics` de l'API et collectées par Prometheus.

* **`api_requests_total` (Counter)**
* **`api_request_latency_seconds` (Histogram)**
* **`data_drift_text_length` (Histogram)**

### 3.2. Outils de Monitoring

* **Prometheus (`api/ia_api/prometheus/`)**
* **Grafana (`api/ia_api/grafana/`)**
    * **Dashboard Personnalisé**
    * **Provisioning**

### 3.3. Procédure d'Installation et d'Utilisation du Monitoring

La stack de monitoring (API, Prometheus, Grafana) peut être déployée localement ou en production via Docker Compose.

1.  **Prérequis :** Docker et Docker Compose installés.
2.  **Configuration :** Les secrets doivent être définis dans un fichier `.env`.
3.  **Lancement local :** `docker-compose up -d`.
4.  **Accès :**
    * API : `http://localhost:8001`
    * Prometheus : `http://localhost:9090`
    * Grafana : `http://localhost:3000` (identifiants par défaut : admin/admin)
5.  **Utilisation :** Les dashboards sont automatiquement chargés dans Grafana.

---

## 4. Stratégie de Tests Automatisés (C9 & C12)

Les tests automatisés sont essentiels pour garantir la qualité et la fiabilité de l'API et du modèle d'IA. Nous utilisons `pytest`.

### 4.1. Tests de l'API (C9)

Les tests de l'API (`tests/api_ia/`) couvrent les fonctionnalités principales et les mécanismes de sécurité :

* **`test_auth.py`**
* **`test_generation.py`**
* **`test_middlewares.py`**
* **`test_monitoring.py`**
* **`test_validation.py`**

Ces tests sont exécutés automatiquement dans le pipeline `ci-cd-ia-api.yml`.

### 4.2. Tests du Modèle et de la Qualité des Données (C12)

Les tests liés au modèle et aux données sont intégrés au pipeline MLOps (`ml_pipeline.yml`) :

* **Tests de Qualité des Données (`tests/data/test_data_quality.py`)**
* **Évaluation du Modèle (`llm/evaluate_model.py`)**
* **Validation Comparative ("Validation Gate")**

### 4.3. Outils et Exécution des Tests

* **`pytest`**
* **Bibliothèques d'évaluation :** `evaluate` et `sacrebleu`
* **Exécution en CI**
* **Test de charge (`tests/api_ia/locustfile.py`)**

---

## 5. Intégration dans une Application Cliente (C10) - *Discussion Conceptuelle*

L'API est conçue pour être facilement consommée par une application cliente.

L'intégration impliquerait :

* **Installation de l'application cliente**
* **Communication avec l'API**
* **Gestion de l'authentification**
* **Intégration des points de terminaison**
* **Adaptations d'interfaces**
* **Accessibilité**
* **Tests d'intégration**

---

## 6. Bonnes Pratiques MLOps et Accessibilité

### 6.1. Principes MLOps Adressés

Ce projet démontre une adhésion forte aux principes MLOps :

* **Automatisation**
* **Reproductibilité**
* **Versionnement**
* **Tests et Validation**
* **Monitoring**
* **Collaboration**

### 6.2. Considérations d'Accessibilité dans la Documentation

Nous nous efforçons de rendre cette documentation accessible via :

* **Structure claire**
* **Langage**
* **Format Markdown**
* **Démonstration**

---

## 7. Conclusion

Ce projet offre une implémentation robuste d'une API pour un modèle d'IA et met en œuvre une chaîne CI/CD/MLOps complète et automatisée. De la qualité des données à l'entraînement, la validation comparative et le déploiement conditionnel, en passant par le monitoring en production, chaque étape est couverte pour garantir la fiabilité et l'efficacité du système. Cette architecture jette les bases d'un système d'IA maintenable et évolutif en production.
```