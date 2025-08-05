// frontend/src/pages/TranslatorPage.test.jsx

import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, test, expect, vi, beforeEach } from 'vitest';

import TranslatorPage from './TranslatorPage';
import LoginPage from './LoginPage'; // On a besoin de la page de login pour tester la redirection
import { authService } from '../services/authService';
import { iaApi } from '../services/api';

// Mock complet des services
vi.mock('../services/authService');
vi.mock('../services/api', () => ({
  iaApi: {
    post: vi.fn(),
  },
}));

// Mock partiel de react-router-dom pour contrôler la navigation lors des tests de redirection
const mockedUsedNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom');
    return {
        ...actual,
        useNavigate: () => mockedUsedNavigate,
    };
});


describe('TranslatorPage', () => {

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('devrait rediriger vers la page de login si l\'utilisateur n\'est pas authentifié', () => {
    // On simule un utilisateur non authentifié
    authService.isAuthenticated.mockReturnValue(false);

    render(
        <BrowserRouter>
            <TranslatorPage />
        </BrowserRouter>
    );

    // Vérification que la navigation a été appelée pour rediriger vers /login
    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login', {
      state: { message: "Veuillez vous connecter pour accéder au traducteur." },
    });
  });

  test('devrait afficher la page du traducteur si l\'utilisateur est authentifié', () => {
    // On simule un utilisateur authentifié
    authService.isAuthenticated.mockReturnValue(true);

    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    // On vérifie qu'un élément clé de la page est bien présent
    expect(screen.getByRole('heading', { name: /traducteur darija/i })).toBeInTheDocument();
  });

  test('devrait appeler l\'API de traduction et afficher le résultat', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);

    // On simule la réponse de l'API de traduction
    const mockResponse = { data: { reponse: 'Salam alikoum' } };
    iaApi.post.mockResolvedValue(mockResponse);

    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    // Simulation de l'interaction utilisateur
    const textarea = screen.getByPlaceholderText(/saisissez votre texte/i);
    await user.type(textarea, 'Bonjour à tous');

    const translateButton = screen.getByRole('button', { name: /traduire/i });
    await user.click(translateButton);

    // Vérification de l'appel API
    expect(iaApi.post).toHaveBeenCalledWith('/generer', {
      texte: 'Bonjour à tous',
      src_lang: 'fra_Latn', // Valeur par défaut
      tgt_lang: 'ary_Arab', // Valeur par défaut
    });
    
    // Vérification que le résultat est bien affiché à l'écran
    expect(await screen.findByText('Salam alikoum')).toBeInTheDocument();
  });

  test('devrait gérer une erreur de l\'API de traduction et afficher un message', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);

    // On simule une réponse en erreur de l'API
    iaApi.post.mockRejectedValue(new Error('API Error'));

    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    await user.type(screen.getByPlaceholderText(/saisissez votre texte/i), 'Test');
    await user.click(screen.getByRole('button', { name: /traduire/i }));
    
    // Vérification que le message d'erreur est bien affiché
    expect(await screen.findByText('Une erreur est survenue lors de la traduction. Veuillez réessayer.')).toBeInTheDocument();
  });

  test('devrait inverser les langues et les textes lors du clic sur le bouton "Inverser"', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    
    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    // Saisie initiale
    const inputArea = screen.getByPlaceholderText(/saisissez votre texte/i);
    await user.type(inputArea, 'Bonjour');

    // On simule une première traduction pour remplir le champ de sortie
    await act(async () => {
        iaApi.post.mockResolvedValue({ data: { reponse: 'Salam' } });
        await user.click(screen.getByRole('button', { name: /traduire/i }));
    });

    // Attendre que le résultat 'Salam' soit affiché
    await screen.findByText('Salam');

    // Clic sur le bouton d'inversion
    const swapButton = screen.getByRole('button', { name: /inverser/i });
    await user.click(swapButton);

    // Vérifications
    // L'ancien texte de sortie ('Salam') est maintenant dans la zone de saisie
    expect(inputArea.value).toBe('Salam');
    
    // L'ancien texte de saisie ('Bonjour') est maintenant dans la zone de sortie
    expect(screen.getByText('Bonjour')).toBeInTheDocument();

    // Vérifier que les menus déroulants ont aussi été inversés
    const selects = screen.getAllByRole('combobox');
    expect(selects[0].value).toBe('ary_Arab'); // Source
    expect(selects[1].value).toBe('fra_Latn'); // Cible
  });

});