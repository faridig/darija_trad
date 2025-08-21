// frontend/src/services/api.js

/**
 * @file Ce fichier centralise la configuration des clients HTTP pour communiquer
 * avec les différentes API backend du projet. Il utilise Axios pour créer des
 * instances pré-configurées, ce qui favorise la modularité et la maintenabilité
 * du code.
 */

import axios from 'axios';

// --- Étape 1 : Configuration dynamique des URLs des API ---

/**
 * Récupère l'URL de base pour l'API de Données.
 *
 * Cette approche "en cascade" permet une configuration flexible :
 * 1.  Elle cherche d'abord une configuration injectée à l'exécution
 *     (via `config.js` généré par le Docker entrypoint). C'est la méthode
 *     privilégiée en production (ex: Kubernetes).
 * 2.  Si elle n'est pas trouvée, elle se rabat sur la variable d'environnement
 *     définie au moment du build (via le fichier `.env`). C'est la méthode
 *     utilisée pour le développement local.
 *
 * @type {string}
 */
const DATA_API_URL = window.runtimeConfig?.VITE_DATA_API_BASE_URL || import.meta.env.VITE_DATA_API_BASE_URL;

/**
 * Récupère l'URL de base pour l'API d'IA, en suivant la même logique
 * de cascade que pour la Data API.
 * @type {string}
 */
const IA_API_URL = window.runtimeConfig?.VITE_IA_API_BASE_URL || import.meta.env.VITE_IA_API_BASE_URL;


// --- Étape 2 : Création des instances Axios ---

/**
 * Instance Axios pré-configurée pour toutes les communications avec la Data API.
 * La `baseURL` est définie ici pour éviter de la répéter dans chaque appel.
 * @type {axios.AxiosInstance}
 */
const dataApi = axios.create({
  baseURL: DATA_API_URL,
});

/**
 * Instance Axios pré-configurée pour toutes les communications avec l'API d'IA.
 * @type {axios.AxiosInstance}
 */
const iaApi = axios.create({
  baseURL: IA_API_URL,
});


// --- Étape 3 : Configuration de la sécurité pour l'API d'IA ---

/**
 * Intercepteur de requête pour l'instance `iaApi`.
 *
 * Un intercepteur est une fonction qui est exécutée par Axios AVANT que chaque
 * requête ne soit réellement envoyée. C'est le mécanisme parfait pour ajouter
 * de manière centralisée et transparente des en-têtes d'authentification.
 *
 * Cela évite d'avoir à ajouter manuellement le token dans chaque appel de fonction
 * qui utilise `iaApi`.
 */
iaApi.interceptors.request.use(
  /**
   * Fonction de succès de l'intercepteur.
   * @param {axios.AxiosRequestConfig} config - La configuration de la requête sur le point d'être envoyée.
   * @returns {axios.AxiosRequestConfig} La configuration modifiée (ou non) de la requête.
   */
  (config) => {
    // On récupère le token JWT depuis le localStorage, où `authService` l'a stocké.
    const token = localStorage.getItem('jwt_token');

    // Si un token existe, on l'ajoute à l'en-tête `Authorization`
    // en respectant le format "Bearer token".
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Il est crucial de toujours retourner la configuration pour que la requête puisse continuer.
    return config;
  },
  /**
   * Fonction d'erreur de l'intercepteur.
   * Se déclenche si une erreur se produit lors de la création de la requête.
   * @param {Error} error - L'erreur survenue.
   * @returns {Promise<Error>} Une promesse rejetée avec l'erreur.
   */
  (error) => {
    return Promise.reject(error);
  }
);


// --- Étape 4 : Exportation des instances ---

/**
 * On exporte les instances `dataApi` et `iaApi` pour qu'elles puissent être
 * importées et utilisées dans d'autres parties de l'application (par exemple,
 * dans `authService.js` ou `TranslatorPage.jsx`).
 */
export { dataApi, iaApi };