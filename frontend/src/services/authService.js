// frontend/src/services/authService.js (Version mise à jour et corrigée)

import { dataApi } from './api';

const TOKEN_KEY = 'jwt_token';

// Fonction de connexion (login)
const login = async (username, password) => {
  // Les données doivent être envoyées en format 'x-www-form-urlencoded'
  // pour correspondre à OAuth2PasswordRequestForm de FastAPI
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await dataApi.post('/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  if (response.data.access_token) {
    // CORRECTION: On utilise localStorage pour la persistance
    localStorage.setItem(TOKEN_KEY, response.data.access_token);
  }
  return response.data; 
};

// Fonction d'inscription (register)
const register = async (username, password) => {
  // Pour cet endpoint, l'API attend un payload JSON standard
  const userData = { username, password };
  const response = await dataApi.post('/register', userData);
  return response.data;
};

// Fonction de déconnexion (logout)
const logout = () => {
  // CORRECTION: On utilise localStorage pour la persistance
  localStorage.removeItem(TOKEN_KEY);
};

// Fonction pour récupérer le token (utile pour vérifier si l'utilisateur est connecté)
const getToken = () => {
  // CORRECTION: On utilise localStorage pour la persistance
  return localStorage.getItem(TOKEN_KEY);
};

// NOUVELLE FONCTION: Vérifie si l'utilisateur est authentifié
const isAuthenticated = () => {
  // Un utilisateur est considéré comme authentifié s'il a un token dans le localStorage
  return !!localStorage.getItem(TOKEN_KEY);
};

// Export de toutes les fonctions utiles pour le reste de l'application
export const authService = {
  register,
  login,
  logout,
  getToken,
  isAuthenticated, // On exporte la nouvelle fonction
};