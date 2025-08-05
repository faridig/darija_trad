// frontend/src/pages/RegisterPage.test.jsx

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { describe, test, expect, vi } from 'vitest';

import RegisterPage from './RegisterPage';
import { authService } from '../services/authService';

// Mock du service d'authentification
vi.mock('../services/authService', () => ({
  authService: {
    register: vi.fn(),
  },
}));

// Mock de react-router-dom pour contrôler la navigation
const mockedNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual, // Conserve toutes les exportations originales
    useNavigate: () => mockedNavigate, // Remplace useNavigate par notre espion
  };
});

describe('RegisterPage', () => {
  // Réinitialise les mocks avant chaque test pour éviter les interférences
  beforeEach(() => {
    vi.clearAllMocks();
  });
  
  test('devrait afficher une erreur si les mots de passe ne correspondent pas', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    // Simulation de la saisie avec des mots de passe différents
    await user.type(screen.getByLabelText(/nom d'utilisateur/i), 'newuser');
    await user.type(screen.getByLabelText('Mot de passe'), 'password123');
    await user.type(screen.getByLabelText(/confirmer le mot de passe/i), 'password456');

    // Simulation du clic sur le bouton
    await user.click(screen.getByRole('button', { name: /s'inscrire/i }));

    // Vérification que le message d'erreur est bien affiché
    expect(await screen.findByText('Les mots de passe ne correspondent pas.')).toBeInTheDocument();
    
    // Vérification cruciale : le service d'inscription ne doit PAS avoir été appelé
    expect(authService.register).not.toHaveBeenCalled();
  });

  test('devrait naviguer vers la page de login avec un message de succès après une inscription réussie', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );
    
    // On simule une réponse de succès du service
    authService.register.mockResolvedValue({ id: 1, username: 'newuser' });

    // Simulation de la saisie valide
    await user.type(screen.getByLabelText(/nom d'utilisateur/i), 'newuser');
    await user.type(screen.getByLabelText('Mot de passe'), 'password123');
    await user.type(screen.getByLabelText(/confirmer le mot de passe/i), 'password123');

    await user.click(screen.getByRole('button', { name: /s'inscrire/i }));

    // Vérification que la redirection a bien été appelée
    expect(mockedNavigate).toHaveBeenCalledWith('/login', {
      state: { message: 'Inscription réussie ! Vous pouvez maintenant vous connecter.' },
    });
  });

  test("devrait afficher une erreur si le nom d'utilisateur est déjà pris (erreur 409)", async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    // On simule une erreur "Conflict" (409) de l'API
    authService.register.mockRejectedValue({ response: { status: 409 } });

    await user.type(screen.getByLabelText(/nom d'utilisateur/i), 'existinguser');
    await user.type(screen.getByLabelText('Mot de passe'), 'password123');
    await user.type(screen.getByLabelText(/confirmer le mot de passe/i), 'password123');
    
    await user.click(screen.getByRole('button', { name: /s'inscrire/i }));
    
    // Vérification que le message d'erreur spécifique est affiché
    expect(await screen.findByText("Ce nom d'utilisateur est déjà pris.")).toBeInTheDocument();
  });

  test("devrait afficher une erreur générique pour une autre défaillance de l'API", async () => {
    const user = userEvent.setup();
    // On simule une erreur générique (différente de 409)
    authService.register.mockRejectedValue(new Error('Internal Server Error'));

    render(
        <BrowserRouter>
        <RegisterPage />
        </BrowserRouter>
    );

    // Simulation de la saisie et du clic
    await user.type(screen.getByLabelText(/nom d'utilisateur/i), 'someuser');
    await user.type(screen.getByLabelText('Mot de passe'), 'password123');
    await user.type(screen.getByLabelText(/confirmer le mot de passe/i), 'password123');
    await user.click(screen.getByRole('button', { name: /s'inscrire/i }));

    // Vérification que le message d'erreur générique est affiché
    expect(await screen.findByText('Une erreur est survenue. Veuillez réessayer.')).toBeInTheDocument();
    });
  
});