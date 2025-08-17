# 🚀 Frontend - Interface de Traduction Darija

Ce module contient l'application frontend de l'outil de traduction, développée avec **React** et **Vite**. Elle fournit une interface utilisateur moderne, réactive et sécurisée pour interagir avec les APIs de données et d'intelligence artificielle.

## ✨ Fonctionnalités Clés

* **Stack Moderne** : **React 19** + **Vite**.
* **Routing Côté Client** : **React Router DOM** pour navigation fluide.
* **Authentification Sécurisée** : Gestion complète JWT, stockage dans `localStorage`.
* **Tests Complets** : **Vitest** + **React Testing Library**.
* **Configuration Dynamique** : `entrypoint.sh` injecte les URLs d'API à l'exécution.
* **Design Élégant** : Palette sombre, UX optimisée.

## 🏗️ Architecture du Frontend

* **`/src`**
  * **`/pages`** : `LoginPage`, `RegisterPage`, `TranslatorPage`.
  * **`/services`** :
    * `api.js` : Instances Axios (`dataApi`, `iaApi`).
    * `authService.js` : Login, register, logout, gestion token.
  * `main.jsx` : Point d'entrée + routage.
  * `App.jsx` : Layout principal.
  * `setupTests.js` : Config tests.

## 🧪 Tests

* **Outils** : Vitest, JSDOM, React Testing Library.
* **Couverture** : ≥ 80%.
* **Cas testés** :
  * Rendu des composants.
  * Interactions utilisateur (clics, saisies).
  * Mock API pour succès/erreurs.
  * Redirections.

Lancement :
```bash
npm test
npm run coverage
```

## 🚀 Démarrage et Déploiement

### Local

**Prérequis** : Node.js + npm.  
**Config** : `.env` avec :
```
VITE_DATA_API_BASE_URL=http://localhost:8000
VITE_IA_API_BASE_URL=http://localhost:8001
```

Installer dépendances :
```bash
npm install
```

Démarrer :
```bash
npm run dev
```
Accès : [http://localhost:5173](http://localhost:5173)

### Production

Build Docker multi-étapes basé sur Nginx :
```bash
docker build -t mon-frontend:latest .
```

Config dynamique à l'exécution :
```bash
docker run -d -p 8080:80   -e VITE_DATA_API_BASE_URL="http://prod-data-api-url.com"   -e VITE_IA_API_BASE_URL="http://prod-ia-api-url.com"   mon-frontend:latest
```

Idéal pour Kubernetes avec ConfigMaps/Secrets.
