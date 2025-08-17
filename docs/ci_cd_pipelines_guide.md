 Guide des Pipelines d'Intégration et Déploiement Continus (CI/CD)

Ce document décrit l'implémentation des chaînes CI/CD pour l'ensemble des composants du projet : **Frontend**, **API IA & Monitoring**, et le **Modèle de Machine Learning**. Il détaille l'approche adoptée pour garantir la qualité, la reproductibilité et l'automatisation de tout le cycle de vie du projet.

---

## 1. Principes Directeurs

Notre stratégie CI/CD repose sur les principes suivants :
*   **Automatisation Complète** : De la validation du code au déploiement en production, chaque étape est scriptée et automatisée via **GitHub Actions**.
*   **Déclencheurs Basés sur les Chemins** : Les pipelines ne se déclenchent que lorsque des fichiers pertinents sont modifiés, optimisant l'utilisation des ressources.
*   **Qualité Intégrée** : Les tests (unitaires, intégration, qualité des données) sont des étapes bloquantes. Aucun code ou modèle de mauvaise qualité n'est déployé.
*   **Déploiement Conditionnel** : Les nouvelles versions (modèles, applications) ne sont déployées que si elles passent toutes les étapes de validation.
*   **Gestion des Secrets** : Toutes les informations sensibles (clés d'API, mots de passe, configurations) sont gérées via les **Secrets GitHub**.

---

## 2. Les Pipelines

Trois workflows principaux orchestrent le cycle de vie du projet.

### 2.1. Pipeline CI/CD du Frontend

*   **Fichier de workflow** : `.github/workflows/ci-cd-frontend.yml`
*   **Objectif** : Gérer le cycle de vie complet de l'application React, des tests au déploiement sur AKS.

*   **Déclencheurs :** `push` et `pull_request` sur la branche `main` pour les modifications dans `frontend/**` ou `k8s/frontend.yaml`.
*   **Jobs et Étapes :**
    1.  **`test-frontend` (CI)** :
        *   Installe les dépendances `npm`.
        *   Exécute les tests unitaires et d'intégration avec **Vitest**.
        *   Génère et upload un rapport de couverture de code.
    2.  **`build-and-push-image` (CD)** :
        *   Ne s'exécute que si les tests réussissent et sur un push vers `main`.
        *   Construit l'image Docker multi-étapes (basée sur Nginx).
        *   Pousse l'image vers **Azure Container Registry (ACR)** avec les tags `latest` et le SHA du commit.
    3.  **`deploy-to-aks` (CD)** :
        *   Ne s'exécute que si le build réussit.
        *   Se connecte au cluster **Azure Kubernetes Service (AKS)**.
        *   Injecte les secrets Kubernetes (`api-secrets`) contenant les URLs des APIs.
        *   Met à jour le manifeste `k8s/frontend.yaml` avec le tag de la nouvelle image.
        *   Applique le manifeste et vérifie la stabilisation du déploiement.

### 2.2. Pipeline CI/CD de l'API IA & Monitoring

*   **Fichier de workflow** : `.github/workflows/ci-cd-ia-api.yml`
*   **Objectif** : Gérer le cycle de vie de l'API FastAPI et de sa stack de monitoring (Prometheus, Grafana).

*   **Déclencheurs :** `push` et `pull_request` sur la branche `main` pour les modifications dans `api/**`, `database/**`, `k8s/**`, etc.
*   **Jobs et Étapes :**
    1.  **`test-api` (CI)** :
        *   Installe les dépendances Python.
        *   Exécute les tests `pytest` sur l'API, avec une exigence de couverture de code de 85%.
    2.  **`build-and-deploy-images` (CD)** :
        *   Ne s'exécute que si les tests réussissent et sur un push vers `main`.
        *   Construit et pousse les 3 images Docker : `ia-api`, `prometheus`, et `grafana` vers ACR.
    3.  **`deploy-to-aks` (CD)** :
        *   **Déploie séquentiellement** les composants sur AKS pour plus de stabilité :
        *   D'abord, l'API IA est déployée et le pipeline attend sa stabilisation (le chargement du modèle peut être long).
        *   Ensuite, les composants de monitoring (Prometheus, Grafana, Alertmanager) sont déployés.
        *   Enfin, l'autoscaler horizontal (HPA) est appliqué à l'API IA, une fois que tout est stable.

### 2.3. Pipeline MLOps du Modèle de Machine Learning

*   **Fichier de workflow** : `.github/workflows/ml_pipeline.yml`
*   **Objectif** : Gérer le cycle de vie complet du modèle de traduction, de l'entraînement au déploiement sur Hugging Face Hub.

*   **Déclencheurs :** `push` sur la branche `main` pour les modifications dans `llm/**` ou `tests/data/**`.
*   **Environnement d'exécution :** Utilise un runner **auto-hébergé (`self-hosted`) avec GPU** pour l'entraînement.
*   **Job Unique `train-validate-and-deploy` :**
    1.  **Préparation & Entraînement** :
        *   Restaure les checkpoints d'entraînement précédents depuis le cache GitHub pour une reprise rapide.
        *   Exporte les données les plus récentes depuis la Data API.
        *   Prépare (divise, équilibre) les datasets.
        *   Valide la qualité des données avec `pytest`.
        *   Lance le **fine-tuning LoRA**, en loggant les métriques sur **MLflow**.
        *   Fusionne l'adaptateur LoRA pour créer un modèle de production complet.
    2.  **Validation Comparative ("Validation Gate")** :
        *   Évalue le **nouveau modèle** sur le jeu de test pour obtenir son score BLEU.
        *   Récupère le score BLEU du **modèle actuellement en production** depuis un fichier `evaluation.json` sur Hugging Face Hub.
        *   **Compare les deux scores**. Le déploiement n'est autorisé que si `nouveau_score > score_production`.
    3.  **Déploiement Conditionnel** :
        *   Si la "Validation Gate" est passée, le nouveau modèle et son fichier d'évaluation sont **automatiquement poussés vers Hugging Face Hub**.
        *   Sinon, le déploiement est annulé, et l'ancien modèle reste en production.
    4.  **Nettoyage** :
        *   À la fin du job (succès ou échec), une étape de nettoyage supprime les anciens caches de checkpoints pour gérer l'espace de stockage.

---

## 3. Conclusion

Cette architecture CI/CD garantit un cycle de développement et de déploiement rapide, fiable et de haute qualité pour tous les composants du projet. Elle permet une itération rapide sur le modèle de Machine Learning tout en maintenant des standards de production élevés pour les applications qui l'exposent.