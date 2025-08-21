// Fichier : frontend/src/pages/TranslatorPage.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { iaApi } from '../services/api';
import { authService } from '../services/authService';
import './TranslatorPage.css';

/**
 * @component SwapIcon
 * @description Composant SVG simple pour l'icône d'inversion des langues.
 */
const SwapIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6.99 11L3 15L6.99 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M3 15H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M17.01 13L21 9L17.01 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M21 9H3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

// =========================================================================
// === POINT CLÉ : Définition des codes de langue pour l'API NLLB =========
// =========================================================================
// Cet objet sert de "mapping" entre les codes techniques requis par le modèle NLLB
// et les noms affichés à l'utilisateur, pour plus de clarté.
const languageMap = {
  fra_Latn: 'Français',
  eng_Latn: 'Anglais',
  ary_Arab: 'Darija',
};

// Génère la liste complète des options pour les menus déroulants.
const allLanguages = Object.keys(languageMap).map(code => ({ code, name: languageMap[code] }));
// =========================================================================

/**
 * @component TranslatorPage
 * @description Page principale de l'application permettant à un utilisateur authentifié
 * de traduire du texte. Gère les états de l'interface, les appels à l'API d'IA,
 * et la logique de l'expérience utilisateur (chargement, erreurs, etc.).
 * C'est le composant central qui démontre l'intégration de l'API (Compétence C10).
 */
function TranslatorPage() {
  // Hook pour la navigation programmatique (redirection).
  const navigate = useNavigate();

  // --- GESTION DE L'ÉTAT DU COMPOSANT (React Hooks) ---
  const [inputText, setInputText] = useState(''); // Texte saisi par l'utilisateur.
  const [outputText, setOutputText] = useState(''); // Texte traduit retourné par l'API.
  const [sourceLang, setSourceLang] = useState('fra_Latn'); // Langue source sélectionnée.
  const [targetLang, setTargetLang] = useState('ary_Arab'); // Langue cible sélectionnée.
  const [isLoading, setIsLoading] = useState(false); // Gère l'affichage du spinner de chargement.
  const [error, setError] = useState(''); // Stocke les messages d'erreur à afficher.
  const [targetLanguages, setTargetLanguages] = useState([]); // Liste dynamique des langues cibles possibles.

  // --- EFFETS DE BORD (React Hooks) ---

  /**
   * @effect
   * @description Vérifie si l'utilisateur est authentifié à chaque rendu du composant.
   * Si l'utilisateur n'est pas connecté, il est redirigé vers la page de login avec un message.
   * C'est une mesure de sécurité pour protéger la route.
   */
  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login', { state: { message: "Veuillez vous connecter pour accéder au traducteur." } });
    }
  }, [navigate]);

  /**
   * @effect
   * @description Met à jour dynamiquement les options du menu de la langue cible
   * en fonction de la langue source sélectionnée.
   * Empêche les combinaisons de langues non supportées par le modèle.
   */
  useEffect(() => {
    let newTargetOptions = [];
    if (sourceLang === 'fra_Latn' || sourceLang === 'eng_Latn') {
      // Si la source est le Français ou l'Anglais, la seule cible possible est le Darija.
      newTargetOptions = [{ code: 'ary_Arab', name: 'Darija' }];
    } else if (sourceLang === 'ary_Arab') {
      // Si la source est le Darija, les cibles possibles sont le Français et l'Anglais.
      newTargetOptions = [
        { code: 'fra_Latn', name: 'Français' },
        { code: 'eng_Latn', name: 'Anglais' },
      ];
    }
    setTargetLanguages(newTargetOptions);

    // Si la langue cible actuellement sélectionnée n'est plus une option valide,
    // on sélectionne la première option disponible par défaut pour éviter une incohérence.
    if (!newTargetOptions.some(lang => lang.code === targetLang)) {
      if (newTargetOptions.length > 0) {
        setTargetLang(newTargetOptions[0].code);
      }
    }
  }, [sourceLang, targetLang]);

  // --- GESTIONNAIRES D'ÉVÉNEMENTS ---

  const handleInputChange = (event) => setInputText(event.target.value);
  const handleSourceLangChange = (event) => setSourceLang(event.target.value);
  const handleTargetLangChange = (event) => setTargetLang(event.target.value);
  
  /**
   * @function handleSwapLanguages
   * @description Inverse les langues source et cible, ainsi que les textes dans les zones de saisie.
   */
  const handleSwapLanguages = () => {
    // La logique d'inversion est possible uniquement si le Darija est l'une des deux langues.
    if (sourceLang === 'ary_Arab' || targetLang === 'ary_Arab') {
      setSourceLang(targetLang);
      setTargetLang(sourceLang);
      setInputText(outputText);
      setOutputText(inputText);
    }
  };
  
  /**
   * @function handleLogout
   * @description Déconnecte l'utilisateur en supprimant son token et le redirige vers la page de login.
   */
  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  /**
   * @async
   * @function handleTranslate
   * @description Fonction principale qui gère l'appel à l'API d'IA pour la traduction.
   * Elle gère l'état de chargement et les cas d'erreur, y compris l'expiration du token.
   * C'est l'implémentation directe de la compétence C10.
   */
  const handleTranslate = async () => {
    // Ne rien faire si le champ de saisie est vide.
    if (!inputText.trim()) return;
    
    // Initialise l'état pour un nouvel appel API.
    setIsLoading(true);
    setError('');
    setOutputText('');
    
    try {
      // Prépare le payload avec les données de l'état du composant.
      const payload = { texte: inputText, src_lang: sourceLang, tgt_lang: targetLang };
      // Appelle le service d'API (qui ajoutera le token JWT automatiquement via son intercepteur).
      const response = await iaApi.post('/generer', payload);
      // Met à jour l'interface avec la traduction reçue.
      setOutputText(response.data.reponse);
    } catch (err) {
      // --- GESTION DES ERREURS ---
      // Ce bloc est crucial pour la robustesse de l'application.
      
      // Cas spécifique : le token a expiré ou est invalide (l'API renvoie 401 Unauthorized).
      if (err.response && err.response.status === 401) {
        // On déconnecte proprement l'utilisateur.
        authService.logout();
        // On le redirige vers la page de login avec un message clair.
        navigate('/login', { state: { message: "Votre session a expiré. Veuillez vous reconnecter." } });
      } else {
        // Pour toutes les autres erreurs (réseau, serveur 500...), on affiche un message générique.
        setError('Une erreur est survenue lors de la traduction. Veuillez réessayer.');
      }
      console.error(err);
    } finally {
      // Assure que l'indicateur de chargement est désactivé, que l'appel ait réussi ou échoué.
      setIsLoading(false);
    }
  };

  // --- RENDU JSX DU COMPOSANT ---
  // La structure HTML/JSX qui sera affichée à l'écran.
  return (
    <div className="translator-page-layout">
      {/* ... (le reste du JSX reste identique) ... */}
    </div>
  );
}

export default TranslatorPage;