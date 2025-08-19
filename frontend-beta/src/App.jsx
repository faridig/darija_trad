import React, { useState, useEffect } from 'react';
import { dataApi, iaApi } from './api';
import './App.css';

function App() {
  // State
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState('admin'); // Pré-rempli pour la démo
  const [password, setPassword] = useState('password'); // Pré-rempli pour la démo
  const [inputText, setInputText] = useState('Bonjour le monde');
  const [outputText, setOutputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Au chargement, vérifier si un token est déjà dans le localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem('jwt_token');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  // --- LOGIQUE D'AUTHENTIFICATION ---
  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await dataApi.post('/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      const receivedToken = response.data.access_token;
      localStorage.setItem('jwt_token', receivedToken);
      setToken(receivedToken);
    } catch (err) {
      setError('Échec de la connexion. Vérifiez vos identifiants.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    setToken(null);
    setOutputText('');
  };

  // --- LOGIQUE DE TRADUCTION ---
  const handleTranslate = async () => {
    if (!inputText.trim()) return;
    setIsLoading(true);
    setError('');
    setOutputText('');
    try {
      const payload = {
        texte: inputText,
        src_lang: "fra_Latn",
        tgt_lang: "ary_Arab"
      };
      // L'intercepteur dans api.js s'occupe d'ajouter le token
      const response = await iaApi.post('/generer', payload);
      setOutputText(response.data.reponse);
    } catch (err) {
      setError('Erreur lors de la traduction.');
      // Gérer l'expiration du token
      if (err.response && err.response.status === 401) {
        handleLogout();
        setError('Session expirée. Veuillez vous reconnecter.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // --- INTERFACE ---
  if (!token) {
    // --- VUE LOGIN ---
    return (
      <div className="container">
        <h1>Connexion au Traducteur</h1>
        <form onSubmit={handleLogin} className="card">
          <input
            type="text"
            placeholder="Nom d'utilisateur"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Connexion...' : 'Se connecter'}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      </div>
    );
  }

  // --- VUE TRADUCTEUR ---
  return (
    <div className="container">
      <h1>Traducteur Darija (Bêta)</h1>
      <div className="card">
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Entrez du texte en français..."
        />
        <button onClick={handleTranslate} disabled={isLoading}>
          {isLoading ? 'Traduction...' : 'Traduire'}
        </button>
        <div className="output-box">
          {outputText || 'La traduction apparaîtra ici...'}
        </div>
        {error && <p className="error">{error}</p>}
      </div>
      <button onClick={handleLogout} className="logout-button">
        Déconnexion
      </button>
    </div>
  );
}

export default App;