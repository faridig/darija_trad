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
    // Récupérer le token depuis le sessionStorage
    const token = sessionStorage.getItem('jwt_token');

    // Si le token existe, on l'ajoute à l'en-tête Authorization
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // On retourne la configuration de la requête pour qu'elle puisse continuer
    return config;
  },
  (error) => {
    // En cas d'erreur lors de la configuration de la requête, on la rejette
    return Promise.reject(error);
  }
);

// On exporte les deux instances pour les utiliser ailleurs dans l'application
export { dataApi, iaApi };