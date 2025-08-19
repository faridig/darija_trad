import axios from 'axios';

// Lecture des URLs depuis les variables d'environnement
const DATA_API_URL = import.meta.env.VITE_DATA_API_BASE_URL;
const IA_API_URL = import.meta.env.VITE_IA_API_BASE_URL;

// Instance pour l'API de données (non authentifiée pour le login)
export const dataApi = axios.create({
  baseURL: DATA_API_URL,
});

// Instance pour l'API d'IA (qui sera authentifiée)
export const iaApi = axios.create({
  baseURL: IA_API_URL,
});

// --- POINT CLÉ DE L'INTÉGRATION (C10) ---
// Intercepteur qui ajoute le token JWT à chaque requête de l'API d'IA
iaApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);