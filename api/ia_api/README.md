# 🤖 IA API - Inférence et Monitoring de Modèle de Traduction

Ce module contient une API haute performance pour l'inférence de traduction Français/Anglais ↔ Darija, construite avec **FastAPI**. Elle est conçue pour être robuste, sécurisée et entièrement **monitorée** grâce à une stack **Prometheus + Grafana**.

L'API délègue les calculs d'inférence à un endpoint externe hébergé sur **Hugging Face**, ce qui la rend légère et facile à déployer.

## ✨ Fonctionnalités Clés

* **API d'Inférence** : Endpoint `/generer` pour traduire du texte.
* **Sécurité Renforcée** : Authentification **JWT**, limitation taille requêtes, en-têtes de sécurité HTTP, rate-limiting.
* **Monitoring Production** :
  * **Prometheus** : Expose `/metrics` sécurisé.
  * **Grafana** : Dashboard pré-configuré.
  * **Alertmanager** : Alertes sur fiabilité, performance, *data drift*.
* **Déploiement Conteneurisé** : **Docker Compose** pour local, scripts pour **Azure Container Registry (ACR)**.
* **Validation des Données** : **Pydantic** pour la validation (`fra_Latn` vs `ary_Arab`).

## 🏛️ Architecture de Monitoring

1. **FastAPI (`app`)** : Endpoints `/generer` et `/metrics`.
2. **Prometheus** : Scrape `/metrics` et évalue les alertes.
3. **Grafana** : Visualisation des métriques.
4. **Alertmanager** : Notifications (email, Slack…).

## 🗺️ Endpoints de l'API

### Inférence (`/generer`)
| Méthode | Endpoint | Sécurité | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/generer` | ✅ JWT | Traduit un texte (`texte`, `src_lang`, `tgt_lang`). |

### Monitoring (`/monitoring`)
| Méthode | Endpoint | Sécurité | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | ✅ JWT | Vérifie disponibilité API et modèle distant. |
| `GET` | `/healthz` | Aucune | Sonde de vivacité pour Kubernetes. |
| `GET` | `/metrics` | ✅ HTTP Basic | Métriques Prometheus (`ADMIN_USERNAME`/`ADMIN_PASSWORD`). |

## 📊 Métriques et Alertes

Métriques :
* `api_requests_total`
* `api_request_latency_seconds`
* `api_http_errors_5xx_total`
* `data_drift_text_length`

Alertes (`prometheus/alert.rules.yml`) :
* `ApiDown`
* `HighErrorRate5xx`
* `HighApiLatency`
* `DataDriftDetected`

## 🚀 Démarrage et Déploiement

### Local

1. **Prérequis** : Docker & Docker Compose.
2. **Config** : `.env` avec (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `HF_TOKEN_AI`, `HF_INFERENCE_ENDPOINT_URL`…).
3. **Lancement** :
    ```bash
    cd api/ia_api/
    docker-compose up --build
    ```
4. **Accès** :
    * API : [http://localhost:8001/docs](http://localhost:8001/docs)
    * Prometheus : [http://localhost:9090](http://localhost:9090)
    * Grafana : [http://localhost:3000](http://localhost:3000) (admin/admin)
    * Alertmanager : [http://localhost:9093](http://localhost:9093)

### Azure

```bash
cd api/ia_api/deploiement/
bash push_to_acr.sh
```

Construit, tag et push les images API, Prometheus, Grafana vers ACR.
