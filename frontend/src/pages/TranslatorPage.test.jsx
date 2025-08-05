// frontend/src/pages/TranslatorPage.test.jsx

import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { describe, test, expect, vi, beforeEach } from 'vitest';

import TranslatorPage from './TranslatorPage';
import { authService } from '../services/authService';
import { iaApi } from '../services/api';

// --- Mocks ---
// On simule les services externes pour isoler le composant
vi.mock('../services/authService');
vi.mock('../services/api', () => ({
  iaApi: {
    post: vi.fn(),
  },
}));

// On simule useNavigate pour pouvoir vérifier les redirections
const mockedUsedNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
    const actual = await importOriginal();
    return {
        ...actual,
        useNavigate: () => mockedUsedNavigate,
    };
});

// --- Début des tests ---
describe('TranslatorPage', () => {

  beforeEach(() => {
    // On réinitialise tous les mocks avant chaque test pour garantir l'isolation
    vi.clearAllMocks();
  });

  test('devrait rediriger vers /login si l\'utilisateur n\'est pas authentifié', () => {
    authService.isAuthenticated.mockReturnValue(false);
    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);
    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login', {
      state: { message: "Veuillez vous connecter pour accéder au traducteur." },
    });
  });

  test('devrait afficher la page du traducteur si l\'utilisateur est authentifié', () => {
    authService.isAuthenticated.mockReturnValue(true);
    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);
    expect(screen.getByRole('heading', { name: /traducteur darija/i })).toBeInTheDocument();
  });

  test('devrait appeler l\'API de traduction et afficher le résultat', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    const mockResponse = { data: { reponse: 'Salam alikoum' } };
    iaApi.post.mockResolvedValue(mockResponse);

    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    const textarea = screen.getByPlaceholderText(/saisissez votre texte/i);
    const translateButton = screen.getByRole('button', { name: /traduire/i });

    await user.type(textarea, 'Bonjour à tous');
    
    // On enveloppe le clic qui déclenche l'appel API asynchrone dans act()
    await act(async () => {
      await user.click(translateButton);
    });
    
    expect(iaApi.post).toHaveBeenCalledWith('/generer', {
      texte: 'Bonjour à tous',
      src_lang: 'fra_Latn',
      tgt_lang: 'ary_Arab',
    });
    
    expect(await screen.findByText('Salam alikoum')).toBeInTheDocument();
  });

  test('devrait gérer une erreur de l\'API de traduction et afficher un message', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    iaApi.post.mockRejectedValue(new Error('API Error'));

    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    await user.type(screen.getByPlaceholderText(/saisissez votre texte/i), 'Test');
    
    // On enveloppe le clic qui déclenche l'appel API asynchrone (qui va échouer)
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /traduire/i }));
    });
    
    expect(await screen.findByText('Une erreur est survenue lors de la traduction. Veuillez réessayer.')).toBeInTheDocument();
  });

  test('devrait inverser les langues et les textes lors du clic sur le bouton "Inverser"', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    
    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    const inputArea = screen.getByPlaceholderText(/saisissez votre texte/i);
    const translateButton = screen.getByRole('button', { name: /traduire/i });

    // Étape 1 : Saisir du texte et le traduire
    await user.type(inputArea, 'Bonjour');
    await act(async () => {
        iaApi.post.mockResolvedValue({ data: { reponse: 'Salam' } });
        await user.click(translateButton);
    });

    // On attend que la première mise à jour soit terminée
    await screen.findByText('Salam');
    
    // Étape 2 : Inverser les langues
    const swapButton = screen.getByRole('button', { name: /inverser/i });
    await act(async () => {
      await user.click(swapButton);
    });
    
    expect(inputArea.value).toBe('Salam');
    expect(screen.getByText('Bonjour')).toBeInTheDocument();
    const selects = screen.getAllByRole('combobox');
    expect(selects[0].value).toBe('ary_Arab');
    expect(selects[1].value).toBe('fra_Latn');
  });

  test('devrait appeler authService.logout et rediriger au clic sur Déconnexion', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);

    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    const logoutButton = screen.getByRole('button', { name: /déconnexion/i });
    // Le clic sur logout est synchrone mais déclenche une navigation, il est bon de l'envelopper aussi.
    await act(async () => {
        await user.click(logoutButton);
    });

    expect(authService.logout).toHaveBeenCalledOnce();
    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login');
  });
  
  test('devrait rediriger vers login avec un message si l\'API renvoie une erreur 401 (session expirée)', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    const apiError = { response: { status: 401 } };
    iaApi.post.mockRejectedValue(apiError);

    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    await user.type(screen.getByPlaceholderText(/saisissez votre texte/i), 'Ce texte va échouer');
    
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /traduire/i }));
    });

    expect(authService.logout).toHaveBeenCalledOnce();
    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login', {
      state: { message: "Votre session a expiré. Veuillez vous reconnecter." },
    });
  });
});