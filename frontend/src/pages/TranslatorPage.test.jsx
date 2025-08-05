// frontend/src/pages/TranslatorPage.test.jsx

import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { describe, test, expect, vi, beforeEach } from 'vitest';

import TranslatorPage from './TranslatorPage';
import { authService } from '../services/authService';
import { iaApi } from '../services/api';

// --- Bloc de Mocks (INCHANGÉ) ---
vi.mock('../services/authService');
vi.mock('../services/api', () => ({
  iaApi: {
    post: vi.fn(),
  },
}));

const mockedUsedNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom');
    return {
        ...actual,
        useNavigate: () => mockedUsedNavigate,
    };
});

// --- Début des tests ---
describe('TranslatorPage', () => {

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // --- Tests existants (INCHANGÉS) ---
  test('devrait rediriger vers la page de login si l\'utilisateur n\'est pas authentifié', () => {
    authService.isAuthenticated.mockReturnValue(false);

    render(
        <BrowserRouter>
            <TranslatorPage />
        </BrowserRouter>
    );

    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login', {
      state: { message: "Veuillez vous connecter pour accéder au traducteur." },
    });
  });

  test('devrait afficher la page du traducteur si l\'utilisateur est authentifié', () => {
    authService.isAuthenticated.mockReturnValue(true);

    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    expect(screen.getByRole('heading', { name: /traducteur darija/i })).toBeInTheDocument();
  });

  // --- Test mis à jour avec act() ---
  test('devrait appeler l\'API de traduction et afficher le résultat', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    const mockResponse = { data: { reponse: 'Salam alikoum' } };
    iaApi.post.mockResolvedValue(mockResponse);

    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    const textarea = screen.getByPlaceholderText(/saisissez votre texte/i);
    const translateButton = screen.getByRole('button', { name: /traduire/i });

    // Envelopper les actions asynchrones dans act()
    await act(async () => {
      await user.type(textarea, 'Bonjour à tous');
      await user.click(translateButton);
    });
    
    expect(iaApi.post).toHaveBeenCalledWith('/generer', {
      texte: 'Bonjour à tous',
      src_lang: 'fra_Latn',
      tgt_lang: 'ary_Arab',
    });
    
    expect(await screen.findByText('Salam alikoum')).toBeInTheDocument();
  });

  // --- Test mis à jour avec act() ---
  test('devrait gérer une erreur de l\'API de traduction et afficher un message', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    iaApi.post.mockRejectedValue(new Error('API Error'));

    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    // Envelopper les actions asynchrones dans act()
    await act(async () => {
      await user.type(screen.getByPlaceholderText(/saisissez votre texte/i), 'Test');
      await user.click(screen.getByRole('button', { name: /traduire/i }));
    });
    
    expect(await screen.findByText('Une erreur est survenue lors de la traduction. Veuillez réessayer.')).toBeInTheDocument();
  });

  // --- Test mis à jour avec act() ---
  test('devrait inverser les langues et les textes lors du clic sur le bouton "Inverser"', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    
    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    const inputArea = screen.getByPlaceholderText(/saisissez votre texte/i);
    const translateButton = screen.getByRole('button', { name: /traduire/i });

    await act(async () => {
        await user.type(inputArea, 'Bonjour');
        iaApi.post.mockResolvedValue({ data: { reponse: 'Salam' } });
        await user.click(translateButton);
    });

    await screen.findByText('Salam');
    const swapButton = screen.getByRole('button', { name: /inverser/i });

    // Envelopper la deuxième action dans act()
    await act(async () => {
      await user.click(swapButton);
    });
    
    expect(inputArea.value).toBe('Salam');
    expect(screen.getByText('Bonjour')).toBeInTheDocument();
    const selects = screen.getAllByRole('combobox');
    expect(selects[0].value).toBe('ary_Arab');
    expect(selects[1].value).toBe('fra_Latn');
  });

  // ==========================================================
  // NOUVEAUX TESTS POUR AUGMENTER LA COUVERTURE
  // ==========================================================

  test('devrait appeler authService.logout et rediriger vers /login au clic sur Déconnexion', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);

    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    const logoutButton = screen.getByRole('button', { name: /déconnexion/i });
    await user.click(logoutButton);

    // Vérifie que la fonction de déconnexion du service a été appelée
    expect(authService.logout).toHaveBeenCalledOnce();
    // Vérifie que l'utilisateur est redirigé vers la page de connexion
    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login');
  });
  
  test('devrait rediriger vers login avec un message si l\'API renvoie une erreur 401 (session expirée)', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);

    // On simule une erreur 401 (Unauthorized) de l'API
    const apiError = { response: { status: 401 } };
    iaApi.post.mockRejectedValue(apiError);

    render(
      <BrowserRouter>
        <TranslatorPage />
      </BrowserRouter>
    );

    const textarea = screen.getByPlaceholderText(/saisissez votre texte/i);
    const translateButton = screen.getByRole('button', { name: /traduire/i });

    await act(async () => {
      await user.type(textarea, 'Ce texte va échouer');
      await user.click(translateButton);
    });

    // Vérifie que la déconnexion a été appelée (bonne pratique en cas de 401)
    expect(authService.logout).toHaveBeenCalledOnce();
    // Vérifie que la redirection se fait vers /login avec le message approprié
    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login', {
      state: { message: "Votre session a expiré. Veuillez vous reconnecter." },
    });
  });

});