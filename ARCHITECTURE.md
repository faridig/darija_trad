# Architecture Technique - Frontend de Traduction

Ce document décrit l'architecture, les technologies et les flux de données pour l'application web frontend du projet de traduction.

## 1. Choix des Technologies et Outils

Le développement de l'application s'appuiera sur un écosystème JavaScript moderne, axé sur la performance, la maintenabilité et une expérience de développement fluide.

| Catégorie | Outil / Technologie | Justification |
| :--- | :--- | :--- |
| **Framework UI** | **React (avec Vite)** | Un standard de l'industrie pour construire des interfaces utilisateur réactives et modulaires. Vite offre un environnement de développement ultra-rapide et une configuration optimisée par défaut. Cette approche est idéale pour une **Single Page Application (SPA)**, offrant une expérience utilisateur fluide sans rechargement de page. |
| **Langage** | **JavaScript (ES6+)** | Le langage natif du navigateur, indispensable pour une application frontend interactive. |
| **Client HTTP** | **Axios** | Une bibliothèque robuste pour effectuer les requêtes HTTP vers notre API backend. Elle gère nativement les promesses et simplifie l'interception des requêtes/réponses (utile pour ajouter le token JWT). |
| **Gestion des Paquets** | **NPM** | Le gestionnaire de paquets par défaut de l'écosystème Node.js. |
| **Conteneurisation** | **Docker** | Permet de packager notre application frontend dans une image portable, garantissant un environnement d'exécution cohérent du développement à la production. |
| **Serveur Web (en prod)** | **Nginx** | Un serveur web haute performance et léger, parfait pour servir les fichiers statiques (HTML, CSS, JS) de notre application React une fois "buildée". |
| **Versionnement** | **Git & GitHub** | Pour le suivi du code source, la collaboration et l'intégration avec les workflows CI/CD. |

### Justification des choix par rapport à d'autres alternatives

Le choix d'une stack basée sur React/Nginx a été fait après avoir considéré d'autres options pertinentes :

-   **Pourquoi pas Django ?**
    Django est un framework backend "full-stack" puissant, écrit en Python. Il est conçu pour gérer à la fois la logique métier, l'accès aux bases de données et le rendu des pages HTML (via des templates). Dans notre cas, **le backend existe déjà** : c'est notre API FastAPI. Utiliser Django pour le frontend serait redondant et contraire au principe de **séparation des préoccupations**. Notre architecture vise un découplage clair entre le client (frontend, en JavaScript) et le serveur (backend API, en Python). React est spécifiquement conçu pour créer des interfaces utilisateur et se connecte parfaitement à n'importe quelle API, ce qui correspond exactement à notre besoin.

-   **Pourquoi pas Streamlit ou Gradio ?**
    Streamlit et Gradio sont des outils fantastiques pour créer rapidement des démonstrations et des interfaces pour des modèles de Machine Learning. Cependant, ils présentent deux limitations pour ce projet :
    1.  **Moins de contrôle sur l'UI/UX :** Ils sont "opinionated", c'est-à-dire qu'ils imposent une structure et un style. Cela rend plus difficile l'implémentation de spécifications d'UI/UX précises et le respect de normes d'accessibilité (WCAG) comme demandé dans nos spécifications. React nous donne un contrôle total sur le HTML, le CSS et le comportement de l'application.
    2.  **Couplage avec Python :** Ces outils sont conçus pour s'exécuter dans le même processus Python que le modèle. Notre modèle est déjà exposé via une API REST sécurisée. L'objectif est de développer un **client indépendant**, qui pourrait être une application web, mobile ou de bureau. Construire un client en React démontre cette indépendance et simule un cas d'usage d'entreprise plus réaliste.

En conclusion, la stack React + Nginx est la plus adaptée pour construire un client web découplé, personnalisable et optimisé pour la production, qui consomme une API IA existante.

## 2. Architecture Applicative et Flux de Données

### 2.1. Schéma d'Architecture sur Kubernetes

L'application est conçue selon une architecture **N-tiers** et déployée sur Azure Kubernetes Service (AKS). La communication entre le client et le serveur est découplée et gérée par les services Kubernetes, qui agissent comme des répartiteurs de charge (load balancers).

![Schéma d'Architecture sur AKS](./docs/architecture/architecture-schema.png) 
*(Nous allons créer ce schéma)*

**Description du schéma :**

1.  **Utilisateur Final :** L'utilisateur accède à l'application via son navigateur web.
2.  **Azure Load Balancer (Frontend) :** Le trafic entrant pour l'application frontend est intercepté par un Load Balancer Azure, provisionné par le `Service` Kubernetes du frontend. Il possède une IP publique et redirige le trafic vers le pod Nginx.
3.  **Pod Frontend (React + Nginx) :** Le conteneur Nginx sert les fichiers statiques de l'application React au navigateur de l'utilisateur.
4.  **Communication Frontend -> Backend :** Lorsque l'utilisateur effectue une action (login, traduction), le code JavaScript (via Axios) dans le navigateur envoie une requête HTTP directement à l'IP publique de l'API.
5.  **Azure Load Balancer (API) :** Un second Load Balancer, provisionné par le `Service` Kubernetes de l'API, reçoit cette requête sur son IP publique.
6.  **Pod Backend (API FastAPI) :** Le Load Balancer transmet la requête au pod de l'API FastAPI, qui la traite.
7.  **Base de Données (Supabase) :** Si nécessaire (pour l'authentification), l'API communique avec la base de données externe PostgreSQL (Supabase).
8.  **Réponse :** La réponse de l'API suit le chemin inverse jusqu'au navigateur de l'utilisateur.

Ce modèle, utilisant deux services `LoadBalancer`, est simple et fonctionnel. Pour des applications plus complexes, un **Ingress Controller** pourrait être utilisé pour unifier le trafic sous une seule adresse IP et gérer des règles de routage avancées.

### 2.2. Flux de Données d'Authentification (JWT)

La sécurité entre le frontend et le backend est assurée par des JSON Web Tokens (JWT).

1.  **Login :** L'utilisateur soumet son `username` et `password` au endpoint `POST /login` de l'API.
2.  **Validation :** L'API vérifie les identifiants dans la base de données.
3.  **Génération du Token :** Si les identifiants sont valides, l'API génère un token JWT signé contenant une date d'expiration.
4.  **Stockage du Token :** Le frontend reçoit le token et le stocke de manière sécurisée dans le navigateur (par exemple, dans le `sessionStorage` ou `localStorage`).
5.  **Requêtes Authentifiées :** Pour toutes les requêtes suivantes vers des endpoints protégés (comme `POST /generer`), le frontend ajoute le token dans l'en-tête HTTP : `Authorization: Bearer <token>`.
6.  **Vérification du Token :** À chaque requête, l'API vérifie la validité de la signature et la date d'expiration du token avant d'autoriser l'accès à la ressource.