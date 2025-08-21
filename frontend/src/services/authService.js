// frontend/src/services/authService.js

/**
 * @file Ce module centralise toute la logique d'authentification de l'application.
 * Il gère l'inscription, la connexion, la déconnexion et la gestion du token JWT.
 * Il interagit exclusivement avec l'API de Données (`dataApi`).
 */

import { dataApi } from './api';

// Clé utilisée pour stocker le token JWT dans le localStorage du navigateur.
// L'utilisation d'une constante évite les erreurs de frappe.
const TOKEN_KEY = 'jwt_token';

/**
 * Tente de connecter un utilisateur en envoyant ses identifiants à l'API.
 * En cas de succès, stocke le token JWT reçu dans le localStorage.
 * @param {string} username Le nom d'utilisateur.
 * @param {string} password Le mot de passe.
 * @returns {Promise<object>} La réponse de l'API, contenant l'access_token.
 * @throws {Error} Lance une erreur si la requête échoue (gérée par Axios).
 */
const login = async (username, password) => {
  // L'endpoint `/login` de FastAPI avec OAuth2PasswordRequestForm attend
  // des données au format 'x-www-form-urlencoded', et non JSON.
  // Nous construisons donc ce format manuellement.
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  // Envoi de la requête à l'API de Données.
  const response = await dataApi.post('/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  // Si l'API renvoie un token, on le sauvegarde.
  if (response.data.access_token) {
    // Le localStorage est utilisé pour que le token persiste même si l'utilisateur
    // ferme l'onglet ou le navigateur, permettant une session "mémorisée".
    localStorage.setItem(TOKEN_KEY, response.data.access_token);
  }
  return response.data; 
};

/**
 * Crée un nouveau compte utilisateur.
 * @param {string} username Le nom d'utilisateur souhaité.
 * @param {string} password Le mot de passe choisi.
 * @returns {Promise<object>} Les informations de l'utilisateur créé (sans le mot de passe).
 * @throws {Error} Lance une erreur si la requête échoue (ex: utilisateur déjà existant).
 */
const register = async (username, password) => {
  // L'endpoint `/register` attend un payload JSON standard.
  const userData = { username, password };
  const response = await dataApi.post('/register', userData);
  return response.data;
};

/**
 * Déconnecte l'utilisateur en supprimant son token JWT du localStorage.
 * Cette action est purement locale au client.
 */
const logout = () => {
  // La suppression du token invalide la session côté client.
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * Récupère le token JWT actuellement stocké.
 * @returns {string|null} Le token JWT s'il existe, sinon null.
 */
const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Vérifie si un utilisateur est actuellement considéré comme authentifié.
 * @returns {boolean} True si un token est présent, sinon false.
 */
const isAuthenticated = () => {
  // La double négation (!!) convertit la valeur (une chaîne ou null) en un booléen strict.
  // Si getItem retourne un token (chaîne non vide), !!token devient true.
  // Si getItem retourne null, !!null devient false.
  return !!localStorage.getItem(TOKEN_KEY);
};

/**
 * Objet exporté contenant toutes les fonctions publiques du service d'authentification.
 * C'est le seul point d'entrée pour les autres parties de l'application (composants React).
 */
export const authService = {
  register,
  login,
  logout,
  getToken,
  isAuthenticated,
};