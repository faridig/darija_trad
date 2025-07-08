# Monitoring du modèle IA – NLLB-LoRA Darija

Ce document présente les métriques exposées par l’API et utilisées pour surveiller le comportement du modèle de traduction français-darija basé sur NLLB avec LoRA.

---

## Objectifs

- Suivre l’utilisation réelle de l’API
- Mesurer les performances du modèle
- Identifier les dérives de données (data drift)
- Prévoir les besoins de réentraînement

---

## Outils utilisés

- **FastAPI** : serveur d’API
- **Prometheus** : collecte des métriques
- **Docker Compose** : orchestration locale
- **Grafana** : visualisation des métriques

---

## Endpoints de monitoring

| Endpoint     | Description                                       | Sécurité            |
|--------------|---------------------------------------------------|---------------------|
| `/metrics`   | Expose les métriques Prometheus                  | ✅ Token HTTP       |
| `/health`    | Vérifie que le modèle répond correctement         | ✅ Token JWT        |

---

## Accès aux métriques Prometheus

L’accès à `/metrics` est restreint via un en-tête HTTP spécifique.

- En-tête requis : `X-Prometheus-Token`
- Valeur : définie dans `.env` via la variable `PROMETHEUS_METRICS_TOKEN`
- Seul Prometheus (ou un outil autorisé) doit y accéder

---

## Métriques collectées

### `api_requests_total`

- Type : Counter  
- Description : Nombre total de requêtes, classées par méthode HTTP et endpoint.

### `api_request_latency_seconds`

- Type : Histogram  
- Description : Durée de traitement des requêtes API, par endpoint.

### `data_drift_text_length`

- Type : Histogram  
- Description : Longueur des textes soumis au modèle (en nombre de mots).  
- Utilité : permet d’observer une dérive potentielle des entrées utilisateur.

---

## Exemple d’interprétation

- Une augmentation des requêtes `/generer` → surutilisation ou test de charge.
- Une latence élevée → saturation ou ralentissement du modèle.
- Une longueur excessive des textes → changement d’usage ou erreur d’intégration.

---

## Accès local aux services

| Service     | URL par défaut             |
|-------------|----------------------------|
| API         | http://localhost:8001      |
| Swagger UI  | http://localhost:8001/docs |
| Prometheus  | http://localhost:9090      |
| Grafana     | http://localhost:3000      |

---
