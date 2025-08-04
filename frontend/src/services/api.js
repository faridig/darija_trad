// frontend/src/services/api.js - VERSION CORRIGÉE

import axios from 'axios';

// Création d'une instance Axios pour l'API de données
const dataApi = axios.create({
  baseURL: import.meta.env.VITE_DATA_API_BASE_URL,
});

// Création d'une instance Axios pour l'API d'IA
const iaApi = axios.create({
  baseURL: import.meta.env.VITE_IA_API_BASE_URL,
});

// Intercepteur pour l'instance de l'API d'IA
iaApi.interceptors.request.use(
  (config) => {
    // CORRECTION : On lit depuis localStorage pour être cohérent avec authService.js
    const token = localStorage.getItem('jwt_token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// On exporte les deux instances pour les utiliser ailleurs dans l'application
export { dataApi, iaApi };