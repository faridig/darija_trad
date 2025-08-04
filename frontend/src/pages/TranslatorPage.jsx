import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { iaApi } from '../services/api';
import { authService } from '../services/authService';
import './TranslatorPage.css';

// Composant pour l'icône SVG
const SwapIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6.99 11L3 15L6.99 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M3 15H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M17.01 13L21 9L17.01 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M21 9H3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

// Source de vérité pour les noms et codes de langue
const languageMap = {
  fra_Latn: 'Français',
  eng_Latn: 'Anglais',
  ary_Arab: 'Darija',
};

// Liste complète des langues pour le menu source
const allLanguages = Object.keys(languageMap).map(code => ({ code, name: languageMap[code] }));

function TranslatorPage() {
  const navigate = useNavigate();

  // Déclaration de tous les états du composant
  const [inputText, setInputText] = useState('');
  const [outputText, setOutputText] = useState('');
  const [sourceLang, setSourceLang] = useState('fra_Latn');
  const [targetLang, setTargetLang] = useState('ary_Arab');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [targetLanguages, setTargetLanguages] = useState([]);

  // Effet pour protéger la route
  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login', { state: { message: "Veuillez vous connecter pour accéder au traducteur." } });
    }
  }, [navigate]);

  // Effet pour gérer la logique des menus
  useEffect(() => {
    let newTargetOptions = [];
    if (sourceLang === 'fra_Latn' || sourceLang === 'eng_Latn') {
      newTargetOptions = [{ code: 'ary_Arab', name: 'Darija' }];
    } else if (sourceLang === 'ary_Arab') {
      newTargetOptions = [
        { code: 'fra_Latn', name: 'Français' },
        { code: 'eng_Latn', name: 'Anglais' },
      ];
    }
    setTargetLanguages(newTargetOptions);
    if (!newTargetOptions.some(lang => lang.code === targetLang)) {
      if (newTargetOptions.length > 0) {
        setTargetLang(newTargetOptions[0].code);
      }
    }
  }, [sourceLang, targetLang]);

  // Gestionnaires pour les interactions utilisateur
  const handleInputChange = (event) => setInputText(event.target.value);
  const handleSourceLangChange = (event) => setSourceLang(event.target.value);
  const handleTargetLangChange = (event) => setTargetLang(event.target.value);
  
  const handleSwapLanguages = () => {
    if (sourceLang === 'ary_Arab' || targetLang === 'ary_Arab') {
      setSourceLang(targetLang);
      setTargetLang(sourceLang);
      setInputText(outputText);
      setOutputText(inputText);
    }
  };
  
  // NOUVEAU: Gestionnaire pour la déconnexion
  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  // Logique d'appel à l'API de traduction
  const handleTranslate = async () => {
    if (!inputText.trim()) return;
    setIsLoading(true);
    setError('');
    setOutputText('');
    try {
      const payload = { texte: inputText, src_lang: sourceLang, tgt_lang: targetLang };
      const response = await iaApi.post('/generer', payload);
      setOutputText(response.data.reponse);
    } catch (err) {
      if (err.response && err.response.status === 401) {
        authService.logout();
        navigate('/login', { state: { message: "Votre session a expiré. Veuillez vous reconnecter." } });
      } else {
        setError('Une erreur est survenue lors de la traduction. Veuillez réessayer.');
      }
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Rendu du composant JSX
  return (
    <div className="translator-page-layout">
      {/* MODIFICATION: Ajout du bouton de déconnexion */}
      <header className="translator-header">
        <h1>Traducteur Darija</h1>
        <button onClick={handleLogout} className="logout-button">Déconnexion</button>
      </header>
      <main className="translator-main">
        <div className="panel input-panel">
          <div className="language-selector">
            <select id="source-lang" value={sourceLang} onChange={handleSourceLangChange} disabled={isLoading}>
              {allLanguages.map(lang => (
                <option key={lang.code} value={lang.code}>{lang.name}</option>
              ))}
            </select>
          </div>
          <textarea
            placeholder="Saisissez votre texte..."
            className="text-area"
            value={inputText}
            onChange={handleInputChange}
            disabled={isLoading}
          />
        </div>
        
        <button 
          className="swap-languages-button" 
          aria-label="Inverser les langues" 
          onClick={handleSwapLanguages} 
          disabled={isLoading || !(sourceLang === 'ary_Arab' || targetLang === 'ary_Arab')}>
          <div className="swap-button-content">
            <SwapIcon />
            <span>Inverser</span>
          </div>
        </button>
        
        <div className="panel output-panel">
          <div className="language-selector">
            <select id="target-lang" value={targetLang} onChange={handleTargetLangChange} disabled={isLoading || targetLanguages.length <= 1}>
              {targetLanguages.map(lang => (
                <option key={lang.code} value={lang.code}>{lang.name}</option>
              ))}
            </select>
          </div>
          <div className="text-area output-text" readOnly>
            {isLoading ? <div className="spinner"></div> : outputText}
          </div>
        </div>
      </main>
      <footer className="translator-footer">
          {error && <p className="error-message">{error}</p>}
          <button className="translate-button" onClick={handleTranslate} disabled={isLoading}>
            {isLoading ? 'Traduction...' : 'Traduire'}
          </button>
      </footer>
    </div>
  );
}

export default TranslatorPage;