import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/authService';

function LoginPage() {
  // Pour la redirection après connexion réussie
  const navigate = useNavigate();

  // Pour récupérer le message de succès après l'inscription
  const location = useLocation();
  const successMessage = location.state?.message;

  // États pour stocker les valeurs des champs et les erreurs
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Fonction appelée lors de la soumission du formulaire
  const handleSubmit = async (event) => {
    event.preventDefault(); // Empêche le rechargement de la page
    setError(''); // Réinitialise les erreurs
    setIsLoading(true); // Affiche l'indicateur de chargement

    try {
      await authService.login(username, password);
      // Si le login réussit, redirige vers la page de traduction
      navigate('/translate');
    } catch (err) {
      // Si l'API renvoie une erreur (ex: 400 Bad Request)
      setError('Nom d\'utilisateur ou mot de passe incorrect.');
    } finally {
      setIsLoading(false); // Cache l'indicateur de chargement
    }
  };

  return (
    <div>
      <h2>Connexion</h2>
      {/* Affiche le message de succès s'il est présent */}
      {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">Nom d'utilisateur :</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">Mot de passe :</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {/* Affiche le message d'erreur s'il y en a un */}
        {error && <p style={{ color: 'red' }}>{error}</p>}

        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Connexion en cours...' : 'Se connecter'}
        </button>
      </form>
      <p>
        Vous n'avez pas de compte ? <Link to="/register">S'inscrire</Link>
      </p>
    </div>
  );
}

export default LoginPage;