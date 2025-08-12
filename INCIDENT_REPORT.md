# Rapport d'Incident : Taux d'Erreurs Élevé sur l'API IA

**Date :** 12/08/2025  
**Service Impacté :** API d'IA (`ia-api-service`)  
**Statut :** **Résolu**

---

### 1. Description de l'Incident

**Détection :**
*   Le **12/08/2025 à 08:24**, le serveur **Prometheus** a détecté une anomalie et a déclenché une alerte `HighErrorRate5xx`.
*  **Prometheus** a immédiatement transmis cette alerte à **Alertmanager**, qui a pris en charge la gestion du cycle de vie de l'alerte.
*   Le tableau de bord **Grafana** a confirmé visuellement le problème, montrant une augmentation soudaine du taux d'erreurs HTTP 500 sur l'endpoint `/generer`.

**Impact :**
*   Les appels à la fonctionnalité de traduction (`/generer`) échouaient systématiquement.
*   Le service de traduction était totalement indisponible pour les utilisateurs finaux.

---

### 2. Analyse de la Cause

L'enquête a été menée en suivant ces étapes :

1.  **Consultation des logs** du pod de l'API IA (`ia-api-deployment`).
2.  Les logs ont immédiatement révélé le message d'erreur suivant, répété à chaque tentative de traduction :

    ```
    ERREUR: Échec de l'appel à l'API Hugging Face : 400 Client Error: Bad Request...
    ```

3.  Cette erreur indiquait que notre API ne parvenait plus à communiquer avec son service externe principal : l'endpoint d'inférence hébergé sur Hugging Face.

**Cause Racine Identifiée :**
La **dépendance externe** (l'endpoint Hugging Face) était **hors service** (état "Paused"). Notre API, ne pouvant la joindre, générait une erreur 500 en cascade.

---

### 3. Actions de Résolution

1.  **Action immédiate :** Reconnexion au dashboard de Hugging Face.
2.  **Correction :** L'endpoint d'inférence a été **réactivé manuellement** (passage de l'état "Paused" à "Running").

Aucune modification du code source n'a été nécessaire pour cet incident.

---

### 4. Validation et Retour à la Normale

*   Après la réactivation de l'endpoint, le test de charge (Locust) a été maintenu en exécution.
*   **Observation :**
    *   Le taux d'erreurs sur Grafana est immédiatement revenu à **0%**.
    *   Prometheus a détecté le retour à la normale et a envoyé un signal de résolution à **Alertmanager**.
    *   **(Nouveau)** **Alertmanager** a marqué l'alerte comme `resolved`.
    *   Les nouvelles requêtes de traduction ont réussi avec un code HTTP 200.

L'incident est considéré comme **clos**.