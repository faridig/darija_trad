// frontend/src/pages/LoginPage.test.jsx

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { describe, test, expect, vi } from 'vitest';

import LoginPage from './LoginPage';
import { authService } from '../services/authService';

// On "mock" (simule) le service d'authentification pour ne pas faire de vrais appels API
// pendant les tests. C'est une pratique essentielle.
vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(), // On remplace la fonction 'login' par une fonction espionne
  },
}));

// On englobe les tests dans un 'describe' pour plus de clarté
describe('LoginPage', () => {

  test('devrait afficher le formulaire de connexion et ses éléments', () => {
    // 1. Rendu du composant
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    // 2. Vérifications (Assertions)
    // On vérifie que les éléments clés sont bien présents à l'écran
    expect(screen.getByRole('heading', { name: /connexion/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/nom d'utilisateur/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/mot de passe/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /se connecter/i })).toBeInTheDocument();
  });

  test('devrait appeler authService.login avec les bonnes informations lors de la soumission', async () => {
    const user = userEvent.setup(); // Initialise le simulateur d'événements utilisateur
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    // 1. Simulation de la saisie utilisateur
    const usernameInput = screen.getByLabelText(/nom d'utilisateur/i);
    const passwordInput = screen.getByLabelText(/mot de passe/i);
    const submitButton = screen.getByRole('button', { name: /se connecter/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');

    // 2. Simulation du clic
    await user.click(submitButton);

    // 3. Vérification que notre service a bien été appelé
    expect(authService.login).toHaveBeenCalledOnce();
    expect(authService.login).toHaveBeenCalledWith('testuser', 'password123');
  });

});