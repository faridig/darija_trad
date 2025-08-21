// frontend/src/pages/LoginPage.jsx

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/authService';
import './AuthPage.css';

/**
 * Composant React représentant la page de connexion.
 * 
 * Ce composant gère l'interface et la logique d'authentification de l'utilisateur.
 * Il inclut :
 * - Un formulaire pour la saisie du nom d'utilisateur et du mot de passe.
 * - La communication avec le service d'authentification (`authService`) pour valider les identifiants.
 * - La gestion des états de l'interface (chargement, messages d'erreur/succès).
 * - La redirection de l'utilisateur après une connexion réussie ou un lien vers l'inscription.
 * 
 * @returns {JSX.Element} Le rendu de la page de connexion.
 */
function LoginPage() {
  // --- HOOKS ---
  // Hook pour la navigation programmatique (ex: après un login réussi).
  const navigate = useNavigate();
  // Hook pour accéder à l'état de la route, notamment pour récupérer des messages
  // passés par d'autres pages (ex: un message de succès après l'inscription).
  const location = useLocation();
  
  // Récupère le message de succès s'il a été passé dans l'état de la navigation.
  const successMessage = location.state?.message;

  // --- GESTION DE L'ÉTAT DU COMPOSANT ---
  // useState pour les champs du formulaire (principe des "controlled components").
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  // useState pour stocker et afficher les messages d'erreur à l'utilisateur.
  const [error, setError] = useState('');
  // useState pour gérer l'état de chargement, crucial pour la GESTION DE L'UI (ex: désactiver le bouton).
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Gère la soumission du formulaire de connexion.
   * Cette fonction est asynchrone car elle effectue un appel réseau.
   * @param {React.FormEvent<HTMLFormElement>} event - L'événement de soumission du formulaire.
   */
  const handleSubmit = async (event) => {
    // Empêche le comportement par défaut du formulaire (rechargement de la page).
    event.preventDefault();
    // Réinitialise les erreurs précédentes avant une nouvelle tentative.
    setError('');
    // Active l'état de chargement pour mettre à jour l'UI (bouton désactivé, texte de chargement).
    setIsLoading(true);

    try {
      // Tente de se connecter en appelant le service d'authentification.
      await authService.login(username, password);
      // En cas de succès, redirige l'utilisateur vers la page principale de l'application.
      navigate('/translate');
    } catch (err) {
      // Si l'authentification échoue (le service lève une erreur), on met à jour l'état d'erreur.
      setError('Nom d\'utilisateur ou mot de passe incorrect.');
    } finally {
      // Le bloc `finally` s'exécute TOUJOURS, que le try ait réussi ou échoué.
      // C'est une pratique robuste pour garantir que l'UI redevient interactive.
      setIsLoading(false);
    }
  };

  // --- Rendu JSX du composant ---
  // Le code ci-dessous décrit la structure et l'apparence de la page.
  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Connexion</h2>
        
        {/* Affichage conditionnel des messages de succès ou d'erreur. */}
        {/* C'est une fonctionnalité clé de React pour rendre l'UI dynamique. */}
        {successMessage && <p className="success-message">{successMessage}</p>}
        {error && <p className="error-message">{error}</p>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Nom d'utilisateur</label>
            {/* L'input est un "composant contrôlé" : sa valeur est liée à l'état React. */}
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {/* Le bouton est désactivé et son texte change pendant le chargement. */}
          {/* C'est une bonne pratique UX pour éviter les soumissions multiples. */}
          <button type="submit" className="auth-button" disabled={isLoading}>
            {isLoading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>
        <p className="switch-link">
          {/* Le composant <Link> de React Router gère la navigation côté client sans recharger la page. */}
          Vous n'avez pas de compte ? <Link to="/register">S'inscrire</Link>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;