// src/main.jsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './App.css'; // On importe le CSS ici pour qu'il soit global

// C'est le code qui dit à React :
// 1. Trouve l'élément HTML avec l'ID "root".
// 2. A l'intérieur de cet élément, affiche le composant "App".
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);