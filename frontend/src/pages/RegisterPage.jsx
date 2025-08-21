// frontend/src/pages/RegisterPage.jsx

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import './AuthPage.css';

/**
 * Composant React pour la page d'inscription des utilisateurs.
 *
 * Ce composant gère l'affichage du formulaire d'inscription, la capture des
 * saisies utilisateur, la validation côté client (correspondance des mots de passe),
 * l'appel au service d'authentification pour créer un nouveau compte, et la gestion
 * des états de l'interface (chargement, erreurs).
 *
 * En cas de succès, il redirige l'utilisateur vers la page de connexion avec un
 * message de confirmation. En cas d'erreur, il affiche un retour visuel approprié.
 *
 * @returns {JSX.Element} Le formulaire d'inscription et sa logique.
 */
function RegisterPage() {
  // Hook pour la navigation programmatique (redirection) après une action.
  const navigate = useNavigate();

  // --- GESTION DE L'ÉTAT DU COMPOSANT ---
  // Chaque `useState` crée une variable d'état pour contrôler une partie de l'UI.
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  // État pour stocker et afficher les messages d'erreur à l'utilisateur.
  const [error, setError] = useState('');
  // État pour gérer l'affichage de chargement et désactiver le bouton de soumission.
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Gère la soumission du formulaire d'inscription.
   * Cette fonction est asynchrone car elle effectue un appel réseau.
   * @param {React.FormEvent<HTMLFormElement>} event - L'événement de soumission du formulaire.
   */
  const handleSubmit = async (event) => {
    // Empêche le rechargement de la page par défaut lors de la soumission du formulaire.
    event.preventDefault();

    // --- VALIDATION CÔTÉ CLIENT ---
    // Première vérification, rapide et immédiate, pour la correspondance des mots de passe.
    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas.');
      return; // Arrête l'exécution si la validation échoue.
    }

    // Réinitialise les erreurs et active l'état de chargement avant l'appel API.
    setError('');
    setIsLoading(true);

    try {
      // Appel au service d'authentification pour enregistrer le nouvel utilisateur.
      await authService.register(username, password);

      // --- GESTION DU SUCCÈS ---
      // Si l'inscription réussit, redirige l'utilisateur vers la page de login.
      // On passe un message dans l'état de la navigation pour une meilleure expérience utilisateur.
      navigate('/login', {
        state: { message: 'Inscription réussie ! Vous pouvez maintenant vous connecter.' },
      });
    } catch (err) {
      // --- GESTION DES ERREURS API ---
      // Gère spécifiquement l'erreur 409 (Conflict), qui signifie que l'utilisateur existe déjà.
      if (err.response && err.response.status === 409) {
        setError('Ce nom d\'utilisateur est déjà pris.');
      } else {
        // Gère toutes les autres erreurs (réseau, serveur 500, etc.).
        setError('Une erreur est survenue. Veuillez réessayer.');
      }
    } finally {
      // Le bloc `finally` s'exécute toujours, que l'appel API ait réussi ou échoué.
      // C'est crucial pour s'assurer que l'état de chargement est bien désactivé.
      setIsLoading(false);
    }
  };

  // --- RENDU DU COMPOSANT ---
  // Le JSX utilise des classes CSS définies dans `AuthPage.css` pour le style.
  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Inscription</h2>
        
        {/* Affichage conditionnel : le message d'erreur n'est rendu que si la variable `error` n'est pas vide. */}
        {error && <p className="error-message">{error}</p>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          {/* Chaque champ de saisie est un "composant contrôlé" : sa valeur est liée à l'état React. */}
          <div className="form-group">
            {/* L'attribut `htmlFor` lie le label à l'input pour l'accessibilité. */}
            <label htmlFor="username">Nom d'utilisateur</label>
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
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirmer le mot de passe</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          {/* Le bouton est désactivé pendant le chargement pour éviter les soumissions multiples. */}
          <button type="submit" className="auth-button" disabled={isLoading}>
            {/* Le texte du bouton change pour fournir un retour visuel à l'utilisateur. */}
            {isLoading ? 'Inscription...' : 'S\'inscrire'}
          </button>
        </form>
        <p className="switch-link">
          {/* Le composant `Link` de react-router-dom permet une navigation côté client sans recharger la page. */}
          Vous avez déjà un compte ? <Link to="/login">Se connecter</Link>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;