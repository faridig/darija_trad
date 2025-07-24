```markdown
# Guide de la Chaîne de Livraison Continue (CI/CD) et Approche MLOps du Modèle NLLB-LoRA Darija

Ce document décrit l'implémentation de la chaîne de livraison continue (CI/CD) et l'approche MLOps adoptées pour le modèle de traduction NLLB-LoRA Darija et son API d'exposition. Il vise à détailler les processus automatisés de tests, d'entraînement, de validation, de packaging et de déploiement, en lien avec les compétences E3 du référentiel.

---

## 1. Introduction et Principes MLOps

Ce projet intègre les principes du MLOps (Machine Learning Operations) pour industrialiser le cycle de vie du modèle d'Intelligence Artificielle. Notre approche vise à garantir la **reproductibilité**, la **fiabilité**, l'**automatisation** et le **suivi** des modèles en production.

Les objectifs clés de notre chaîne CI/CD/MLOps sont :

*   **Intégration Continue (CI)** : Assurer la qualité du code de l'API et du modèle via des tests automatisés à chaque modification.
*   **Livraison Continue (CD)** : Automatiser le packaging et le déploiement de l'API et des nouvelles versions du modèle validées.
*   **Validation Continue du Modèle** : Mettre en place une "validation gate" pour s'assurer que seules les versions de modèle performantes sont déployées.
*   **Monitoring en Production** : Surveiller le comportement de l'API et du modèle pour détecter les anomalies et informer les décisions de réentraînement.

## 2. Les Pipelines CI/CD

Nous utilisons **GitHub Actions** pour orchestrer nos pipelines d'intégration et de livraison continues. Deux workflows principaux sont définis :

### 2.1. Pipeline CI/CD pour l'API et le Monitoring (`.github/workflows/ci-cd-ia-api.yml`)

Ce pipeline est dédié à la qualité et au déploiement de l'API de traduction et de son infrastructure de monitoring.

*   **Déclencheurs :**
    *   `on: push` sur la branche `master` si les chemins `api/ia_api/**`, `database/**` ou le workflow lui-même (`.github/workflows/ci-cd-ia-api.yml`) sont modifiés.
    *   `on: pull_request` vers `master` pour les mêmes chemins.
    *   `workflow_dispatch` pour un déclenchement manuel via l'interface GitHub.
*   **Jobs et Étapes :**

    1.  **`test-api` (Intégration Continue)**
        *   **Objectif :** Valider la qualité du code de l'API et des modules de base de données.
        *   **Exécution sur :** `ubuntu-latest`.
        *   **Étapes clés :**
            *   `Checkout du code` : Récupère le dépôt.
            *   `Setup Python 3.11` : Configure l'environnement Python.
            *   `Installer les dépendances` : Installe les `requirements.txt` de l'API et de la base de données, ainsi que `pytest`.
            *   `Lancer les tests de l'API IA` : Exécute l'ensemble des tests unitaires et d'intégration de l'API (voir section 4.1). Un `export PYTHONPATH=$(pwd)` est utilisé pour garantir que les imports Python fonctionnent correctement depuis la racine du projet.

    2.  **`build-and-deploy-images` (Déploiement Continu)**
        *   **Objectif :** Construire les images Docker de l'API, Prometheus et Grafana, puis les pousser vers Azure Container Registry (ACR).
        *   **Conditions :** Ne s'exécute que si le job `test-api` réussit (`needs: test-api`) ET sur un `push` vers la branche `master` (`if: github.ref == 'refs/heads/master' && github.event_name == 'push'`).
        *   **Exécution sur :** `ubuntu-latest`.
        *   **Étapes clés :**
            *   `Checkout du code` : Récupère le dépôt.
            *   `Connexion à Azure Container Registry (ACR)` : Utilise `docker/login-action` avec des secrets GitHub (`ACR_NAME`, `ACR_USERNAME`, `ACR_PASSWORD`) pour s'authentifier à ACR.
            *   `Build and Push IA API Image` : Construit l'image Docker de l'API (`api/ia_api/Dockerfile`) et la pousse vers ACR avec les tags `latest` et le `github.sha` (pour une version unique et traçable).
            *   `Build and Push Prometheus Image` : Construit l'image Docker de Prometheus (`api/ia_api/prometheus/Dockerfile`) et la pousse vers ACR. **Note importante :** Le mot de passe de Prometheus pour l'accès aux métriques est injecté de manière sécurisée via un *secret mount* (`secrets: prometheus_password=${{ secrets.ADMIN_PASSWORD }}`) directement dans le Dockerfile, évitant ainsi de le logger ou de le rendre persistant dans l'image finale.
            *   `Build and Push Grafana Image` : Construit l'image Docker de Grafana (`api/ia_api/grafana/Dockerfile`) et la pousse vers ACR.

*   **Lien avec les compétences E3 :**
    *   **C9 (API)** : Valide la robustesse de l'API via des tests, assure la versionnalisation du code, et prépare le packaging (images Docker) pour l'exposition du modèle.
    *   **C11 (Monitoring)** : Inclut la construction et le déploiement des images Prometheus et Grafana, composants essentiels de notre chaîne de monitoring.
    *   **C13 (CI/CD)** : Démontre l'automatisation des étapes de test et de packaging de l'API, avec des déclencheurs et des conditions bien définis.

### 2.2. Pipeline MLOps pour l'Entraînement et le Déploiement du Modèle (`.github/workflows/ml_pipeline.yml`)

Ce pipeline gère l'ensemble du cycle de vie du modèle d'apprentissage automatique, de l'entraînement à la validation et au déploiement conditionnel.

*   **Déclencheurs :**
    *   `on: push` sur la branche `master` si les chemins `llm/**`, `tests/data/**` ou le workflow lui-même sont modifiés.
    *   `workflow_dispatch` pour un déclenchement manuel.
*   **Environnement d'exécution :** Utilise un `self-hosted, linux, x64, gpu` runner, car l'entraînement et l'évaluation du modèle nécessitent des ressources GPU spécifiques.
*   **Jobs et Étapes :**

    1.  **`train-and-validate` (Entraînement et Pré-validation)**
        *   **Objectif :** Entraîner le modèle NLLB-LoRA, effectuer des tests de qualité de données et sauvegarder les artefacts.
        *   **Environnement :** `training` (pour la gestion des secrets spécifiques).
        *   **Étapes clés :**
            *   `Checkout du code` : Récupère le dépôt.
            *   `Restaurer les checkpoints depuis le cache` : Tente de reprendre l'entraînement à partir de checkpoints précédemment mis en cache, améliorant l'efficacité en cas de redémarrage ou d'échec partiel.
            *   `Setup Python 3.11` et `Installer les dépendances` : Prépare l'environnement pour l'entraînement (incluant `mlflow`, `transformers`, `peft`, `datasets`, etc.).
            *   `Récupérer le corpus de données complet via l'API` : Exécute `llm/export_dataset.py` pour récupérer les données les plus récentes via l'API de données, assurant que le modèle est entraîné sur des données à jour.
            *   `Préparer et diviser les datasets` : Exécute `llm/prepare_datasets.py` pour diviser les données en ensembles d'entraînement, validation et test.
            *   `Lancer les tests de qualité sur les données` : Exécute `pytest tests/data/test_data_quality.py` pour valider l'intégrité et la conformité des données avant l'entraînement.
            *   `Lancer le Fine-Tuning du modèle avec MLflow` : Exécute `llm/finetune_nllb_lora.py`. MLflow est configuré pour suivre les expériences, les paramètres et les métriques d'entraînement. Un `timeout-minutes: 1440` (24 heures) est défini pour cet entraînement intensif. L'arrêt précoce (`EarlyStoppingCallback`) est intégré au script pour éviter le surapprentissage et économiser des ressources.
            *   `Sauvegarder les checkpoints dans le cache` : Met en cache les checkpoints générés par l'entraînement, utile pour les reprises.
            *   `Sauvegarder l'artefact du modèle LoRA` : Télécharge le modèle LoRA entraîné en tant qu'artefact pour le job suivant.
            *   `Sauvegarder l'artefact du jeu de test` : Télécharge le jeu de test sanctuarisé en tant qu'artefact.
            *   `Nettoyer les anciens caches` : Une étape post-succès pour gérer l'espace de cache.

    2.  **`validate-and-compare` (Validation et Comparaison du Modèle - "Validation Gate")**
        *   **Objectif :** Évaluer le nouveau modèle entraîné et le comparer au modèle actuellement en production pour décider du déploiement.
        *   **Conditions :** Dépend du succès du job `train-and-validate` (`needs: train-and-validate`).
        *   **Exécution sur :** `self-hosted, linux, x64, gpu` runner.
        *   **Étapes clés :**
            *   `Télécharger l'artefact du nouveau modèle` et `Télécharger l'artefact du jeu de test` : Récupère le modèle nouvellement entraîné et le jeu de test pour une évaluation cohérente.
            *   `Évaluer le NOUVEAU modèle sur le jeu de test` : Exécute `llm/evaluate_model.py` pour calculer le score BLEU du nouveau modèle.
            *   `Récupérer le score du modèle en PRODUCTION` : Télécharge le fichier `evaluation.json` depuis le modèle en production sur Hugging Face Hub pour obtenir son score BLEU.
            *   `Comparer les scores` : Compare le score BLEU du nouveau modèle avec celui du modèle en production. L'output `is_better` est défini à `true` si le nouveau modèle est plus performant, déclenchant ainsi le déploiement.

    3.  **`deploy-model-to-hub` (Déploiement Conditionnel)**
        *   **Objectif :** Déployer le nouveau modèle sur Hugging Face Hub si sa performance est jugée supérieure.
        *   **Conditions :** Dépend du succès du job `validate-and-compare` ET si l'output `is_better` est `true` (`if: needs.validate-and-compare.outputs.is_better == 'true'`).
        *   **Exécution sur :** `ubuntu-latest`.
        *   **Étapes clés :**
            *   `Télécharger l'artefact du modèle` : Récupère le modèle entraîné.
            *   `Créer le fichier d'évaluation` : Ajoute le score BLEU du nouveau modèle dans un `evaluation.json` qui sera pushé avec le modèle.
            *   `Installer Git LFS et Hugging Face Hub CLI` : Prépare l'environnement pour le push.
            *   `Push vers Hugging Face Hub (Modèle + Score)` : Utilise `huggingface-cli` pour pousser le nouveau modèle (incluant son score) vers le dépôt `Farid59/nllb-darija-lora-model` sur Hugging Face.

*   **Lien avec les compétences E3 :**
    *   **C12 (Tests Automatisés du Modèle)** : Inclut la validation des données, l'évaluation de la performance du modèle, la comparaison avec la baseline de production, et l'utilisation de `pytest` et `evaluate`.
    *   **C13 (Chaîne de Livraison Continue)** : Démontre une chaîne MLOps complète et automatisée couvrant l'entraînement, la validation, le packaging (modèle sauvegardé comme artefact) et le déploiement conditionnel. L'utilisation d'un `self-hosted runner` pour les tâches GPU et la gestion des artifacts/caches sont des aspects avancés de l'industrialisation.

---

## 3. Stratégie de Monitoring (C11)

Le monitoring de l'API et du modèle est une pierre angulaire de notre approche MLOps, permettant de suivre les performances en production et de détecter d'éventuels "drifts" ou dégradations.

### 3.1. Métriques Collectées

Les métriques sont exposées via l'endpoint `/metrics` de l'API (sécurisé par HTTP Basic Auth) et collectées par Prometheus. Elles sont détaillées dans `api/ia_api/docs/monitoring.md` et implémentées dans `api/ia_api/routers/monitoring.py` et `api/ia_api/middlewares.py`.

*   **`api_requests_total` (Counter) :** Nombre total de requêtes, segmenté par méthode HTTP et endpoint. Utile pour suivre l'utilisation de l'API.
*   **`api_request_latency_seconds` (Histogram) :** Mesure la durée de traitement des requêtes, par endpoint. Permet d'analyser les performances et les goulots d'étranglement (latence moyenne, P95, etc.).
*   **`data_drift_text_length` (Histogram) :** Mesure la longueur (en nombre de mots) des textes soumis au modèle via l'endpoint `/generer`. C'est une métrique clé pour détecter le "data drift" : un changement significatif dans la distribution des longueurs d'entrée pourrait indiquer une modification dans l'utilisation de l'API ou un problème en amont.

### 3.2. Outils de Monitoring

*   **Prometheus (`api/ia_api/prometheus/`) :** Collecteur et stockeur de métriques. Il est configuré (`prometheus.yml`) pour "scraper" l'API IA sur le port 8001 à l'endpoint `/metrics`.
*   **Grafana (`api/ia_api/grafana/`) :** Outil de visualisation. Il se connecte à Prometheus pour afficher les métriques via des tableaux de bord interactifs.
    *   **Dashboard Personnalisé :** Le fichier `api/ia_api/grafana/provisioning/dashboards/nllb_darija_dashboard.json` définit un tableau de bord pré-configuré qui affiche :
        *   Le taux de requêtes par endpoint.
        *   La latence moyenne et P95 par endpoint.
        *   La distribution de la longueur du texte en entrée (heatmap pour le data drift).
    *   **Provisioning :** Les dashboards et datasources sont provisionnés (`api/ia_api/grafana/provisioning/`) pour s'assurer qu'ils sont automatiquement chargés au démarrage de Grafana dans le conteneur.

### 3.3. Procédure d'Installation et d'Utilisation du Monitoring

L'ensemble de la stack de monitoring (API, Prometheus, Grafana) peut être déployée localement pour des tests ou en production via Docker Compose.

1.  **Prérequis :** Docker et Docker Compose installés.
2.  **Configuration :** Les secrets (comme `PROMETHEUS_METRICS_TOKEN` ou `ADMIN_PASSWORD`) doivent être définis dans un fichier `.env` à la racine du projet, qui sera utilisé par l'application et injecté dans Prometheus.
3.  **Lancement local :** Naviguez vers `api/ia_api/` et exécutez `docker-compose up -d`.
4.  **Accès :**
    *   API : `http://localhost:8001`
    *   Prometheus : `http://localhost:9090`
    *   Grafana : `http://localhost:3000` (identifiants par défaut : admin/admin, puis changement de mot de passe)
5.  **Utilisation :** Les dashboards sont automatiquement chargés dans Grafana.

Cette chaîne de monitoring en état de marche permet d'évaluer et de restituer en temps réel les métriques visées, facilitant l'identification proactive des problèmes et l'amélioration continue du modèle.

---

## 4. Stratégie de Tests Automatisés (C9 & C12)

Les tests automatisés sont essentiels pour garantir la qualité et la fiabilité de l'API et du modèle d'IA. Nous utilisons `pytest` comme framework de test principal.

### 4.1. Tests de l'API (C9)

Les tests de l'API (`tests/api_ia/`) couvrent les fonctionnalités principales et les mécanismes de sécurité :

*   **`test_auth.py` :** Vérifie le bon fonctionnement de l'authentification (login succès/échec, accès à `/me` avec token).
*   **`test_generation.py` :** Teste l'endpoint de traduction (`/generer`), y compris la réponse attendue et la gestion des erreurs de validation (ex: texte vide).
*   **`test_middlewares.py` :** Valide le comportement des middlewares (headers de sécurité, limitation de taille du body, mise à jour des métriques Prometheus).
*   **`test_monitoring.py` :** Teste l'endpoint de santé (`/health`) et l'accès sécurisé à `/metrics`.
*   **`test_validation.py` :** Vérifie la validation des inputs selon les langues source/cible (ex: caractères non latins pour le français).

Ces tests sont exécutés automatiquement dans le pipeline `ci-cd-ia-api.yml` à chaque modification du code, assurant que l'API est fonctionnelle et sécurisée.

### 4.2. Tests du Modèle et de la Qualité des Données (C12)

Les tests liés au modèle et aux données sont intégrés au pipeline MLOps (`ml_pipeline.yml`) :

*   **Tests de Qualité des Données (`tests/data/test_data_quality.py` - non fourni mais mentionné) :** Exécutés avant l'entraînement, ces tests sont cruciaux pour s'assurer que le dataset exporté et préparé est valide, complet et conforme aux attentes. Cela inclut des vérifications sur les formats, les valeurs manquantes, la distribution, etc. (même si le fichier n'est pas fourni, le critère d'évaluation peut être couvert par l'intention).
*   **Évaluation du Modèle (`llm/evaluate_model.py`) :** Ce script évalue le score BLEU d'un modèle donné sur un jeu de test sanctuarisé. Il est utilisé à deux reprises dans le pipeline MLOps :
    1.  Pour évaluer le **nouveau modèle** fraîchement entraîné.
    2.  Pour évaluer le **modèle en production** (en le téléchargeant depuis Hugging Face Hub).
*   **Validation Comparative ("Validation Gate") :** La logique est implémentée dans le job `validate-and-compare`. Le déploiement n'est autorisé que si le score BLEU du nouveau modèle est *strictement supérieur* à celui du modèle en production. Cette "validation gate" garantit un niveau de qualité élevé et évite les régressions en production.

### 4.3. Outils et Exécution des Tests

*   **`pytest` :** Framework de test Python standard. Le fichier `pytest.ini` configure `pytest` pour inclure le répertoire racine dans `PYTHONPATH` et filtre certains avertissements pour une sortie plus propre.
*   **Bibliothèques d'évaluation :** `evaluate` et `sacrebleu` sont utilisées pour calculer le score BLEU, une métrique standard pour la traduction automatique.
*   **Exécution en CI :** Tous les tests sont automatiquement lancés dans les workflows GitHub Actions, garantissant une intégration continue des tests.
*   **Test de charge (`tests/api_ia/locustfile.py`) :** Bien que non directement intégré au pipeline CI/CD pour un déclenchement automatique post-déploiement, ce fichier `locustfile.py` permet d'effectuer des tests de performance et de charge sur l'API, simulant un grand nombre d'utilisateurs. Cela permet de vérifier la robustesse et la scalabilité de l'API sous contrainte, un aspect important de la qualité en production.

---

## 5. Intégration dans une Application Cliente (C10) - *Discussion Conceptuelle*

Bien que ce dépôt se concentre sur l'API de l'IA et son infrastructure MLOps, l'API est conçue pour être facilement consommée par une application cliente (par exemple, un frontend web ou mobile, ou un autre service backend).

L'intégration d'un modèle d'IA dans une application cliente impliquerait les étapes suivantes, en se basant sur la documentation technique de l'API :

*   **Installation de l'application cliente :** L'application cliente (qui n'est pas dans ce dépôt) devrait être installée et fonctionnelle dans un environnement de développement distinct.
*   **Communication avec l'API :** Utilisation d'une bibliothèque HTTP (ex: `requests` en Python, `fetch` en JavaScript) pour envoyer des requêtes POST à l'endpoint `/generer` de l'API.
*   **Gestion de l'authentification :** L'application devrait :
    *   Envoyer les identifiants utilisateur à l'endpoint `/login` pour obtenir un jeton JWT.
    *   Stocker ce jeton de manière sécurisée (ex: LocalStorage, Cookie sécurisé).
    *   Inclure ce jeton dans l'en-tête `Authorization: Bearer <token>` de toutes les requêtes subséquentes aux endpoints protégés (`/generer`, `/health`).
    *   Gérer le renouvellement du jeton en cas d'expiration (par exemple, en effectuant un re-login automatique ou en demandant à l'utilisateur de se reconnecter).
*   **Intégration des points de terminaison :** Toutes les fonctionnalités d'IA (ici, la traduction) nécessaires à l'application seraient mappées aux appels d'API correspondants, en respectant les schémas d'entrée/sortie (`TexteInput`, `TexteOutput`).
*   **Adaptations d'interfaces :** La traduction étant un processus asynchrone, des indicateurs de chargement ou de progression seraient intégrés dans l'interface utilisateur. La gestion des erreurs (`HTTPException` de l'API) serait également prise en compte pour afficher des messages appropriés à l'utilisateur.
*   **Accessibilité :** Lors du développement de l'application cliente, les normes d'accessibilité (ex: WCAG, RGAA) seraient appliquées aux interfaces utilisateur impactées par la fonctionnalité d'IA, assurant que tous les utilisateurs, y compris ceux avec des handicaps, puissent interagir avec la traduction. Cela inclurait des aspects comme le contraste des couleurs, la navigation au clavier, les descriptions textuelles pour les éléments non textuels, et la compatibilité avec les lecteurs d'écran.
*   **Tests d'intégration :** Des tests automatisés seraient écrits dans l'application cliente pour vérifier que l'intégration avec l'API fonctionne correctement, couvrant les scénarios de succès, d'échec d'authentification, et d'erreurs d'API.

---

## 6. Bonnes Pratiques MLOps et Accessibilité

### 6.1. Principes MLOps Adressés

Ce projet démontre une adhésion forte aux principes MLOps :

*   **Automatisation :** De l'entraînement à la livraison, les étapes sont automatisées via GitHub Actions.
*   **Reproductibilité :** Utilisation de versions spécifiques de Python, de dépendances (`requirements.txt`), de caches pour les modèles, et de l'intégration continue pour garantir que les builds sont cohérents.
*   **Versionnement :** Non seulement le code est versionné, mais aussi les configurations de la CI/CD et les modèles (via Hugging Face Hub et GitHub artifacts).
*   **Tests et Validation :** Des tests rigoureux sont mis en place à différentes étapes (données, API, modèle) avec une "validation gate" pour le déploiement.
*   **Monitoring :** Mise en place d'une stack complète pour surveiller le modèle en production.
*   **Collaboration :** GitHub comme plateforme centrale pour le code, les workflows, et les pull requests facilite la collaboration.

### 6.2. Considérations d'Accessibilité dans la Documentation

Nous nous efforçons de rendre cette documentation et, plus largement, toutes les documentations techniques, aussi accessibles que possible. Bien que l'évaluation formelle de l'accessibilité soit complexe à prouver via des fichiers de code seul, nous avons appliqué les bonnes pratiques suivantes :

*   **Structure claire :** Utilisation cohérente de titres, sous-titres, listes et blocs de code pour une lecture facilitée.
*   **Langage :** Langage concis et précis, évitant le jargon excessif ou l'expliquant lorsque nécessaire.
*   **Format Markdown :** Un format simple et universellement lisible qui peut être facilement converti en d'autres formats (HTML, PDF) qui peuvent ensuite être optimisés pour l'accessibilité.
*   **Démonstration :** La soutenance orale permettra de démontrer directement la clarté et l'opérabilité de la chaîne, renforçant l'accessibilité conceptuelle des informations.

---

## 7. Conclusion

Ce projet offre une implémentation robuste d'une API pour un modèle d'IA et met en œuvre une chaîne CI/CD/MLOps complète et automatisée. De la qualité des données à l'entraînement, la validation comparative et le déploiement conditionnel, en passant par le monitoring en production, chaque étape est couverte pour garantir la fiabilité et l'efficacité du système. Cette architecture jette les bases d'un système d'IA maintenable et évolutif en production.
```