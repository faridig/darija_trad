// frontend/src/pages/TranslatorPage.test.jsx (VERSION CORRIGÉE ET COMPLÈTE)

import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { describe, test, expect, vi, beforeEach } from 'vitest';

import TranslatorPage from './TranslatorPage';
import { authService } from '../services/authService';
import { iaApi } from '../services/api';

// --- Mocks ---
// On simule les services externes pour isoler le composant.
vi.mock('../services/authService');
vi.mock('../services/api', () => ({
  iaApi: {
    post: vi.fn(),
  },
}));

// On simule useNavigate pour pouvoir vérifier les redirections.
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
    // On réinitialise tous les mocks avant chaque test pour garantir l'isolation.
    vi.clearAllMocks();
  });

  // Ce test est correct car il vérifie une redirection (un effet de bord) et non le rendu.
  test('devrait rediriger vers /login si l\'utilisateur n\'est pas authentifié', () => {
    authService.isAuthenticated.mockReturnValue(false);
    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);
    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login', {
      state: { message: "Veuillez vous connecter pour accéder au traducteur." },
    });
  });

  // CORRIGÉ : On passe le test en async et on utilise findByRole.
  test('devrait afficher la page du traducteur si l\'utilisateur est authentifié', async () => {
    authService.isAuthenticated.mockReturnValue(true);
    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);
    // `findByRole` attend que l'élément apparaisse dans le DOM.
    expect(await screen.findByRole('heading', { name: /traducteur darija/i })).toBeInTheDocument();
  });

  // CORRIGÉ : On utilise findBy... pour attendre les éléments.
  test('devrait appeler l\'API de traduction et afficher le résultat', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    const mockResponse = { data: { reponse: 'Salam alikoum' } };
    iaApi.post.mockResolvedValue(mockResponse);

    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    // `findByPlaceholderText` attend que le textarea soit rendu.
    const textarea = await screen.findByPlaceholderText(/saisissez votre texte/i);
    const translateButton = screen.getByRole('button', { name: /traduire/i });

    await user.type(textarea, 'Bonjour à tous');
    
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

  // CORRIGÉ : On utilise findBy...
  test('devrait gérer une erreur de l\'API de traduction et afficher un message', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    iaApi.post.mockRejectedValue(new Error('API Error'));

    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    const textarea = await screen.findByPlaceholderText(/saisissez votre texte/i);
    await user.type(textarea, 'Test');
    
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /traduire/i }));
    });
    
    expect(await screen.findByText('Une erreur est survenue lors de la traduction. Veuillez réessayer.')).toBeInTheDocument();
  });

  // CORRIGÉ : On utilise findBy...
  test('devrait inverser les langues et les textes lors du clic sur le bouton "Inverser"', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    
    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    const inputArea = await screen.findByPlaceholderText(/saisissez votre texte/i);
    const translateButton = screen.getByRole('button', { name: /traduire/i });

    await user.type(inputArea, 'Bonjour');
    await act(async () => {
        iaApi.post.mockResolvedValue({ data: { reponse: 'Salam' } });
        await user.click(translateButton);
    });

    await screen.findByText('Salam');
    
    const swapButton = screen.getByRole('button', { name: /inverser/i });
    await act(async () => {
      await user.click(swapButton);
    });
    
    expect(inputArea.value).toBe('Salam');
    expect(screen.getByText('Bonjour')).toBeInTheDocument();
    // On attend que les selects soient rendus pour les trouver.
    const selects = await screen.findAllByRole('combobox');
    expect(selects[0].value).toBe('ary_Arab');
    expect(selects[1].value).toBe('fra_Latn');
  });

  // CORRIGÉ : On utilise findBy...
  test('devrait appeler authService.logout et rediriger au clic sur Déconnexion', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);

    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    const logoutButton = await screen.findByRole('button', { name: /déconnexion/i });
    await act(async () => {
        await user.click(logoutButton);
    });

    expect(authService.logout).toHaveBeenCalledOnce();
    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login');
  });
  
  // CORRIGÉ : On utilise findBy...
  test('devrait rediriger vers login avec un message si l\'API renvoie une erreur 401 (session expirée)', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    const apiError = { response: { status: 401 } };
    iaApi.post.mockRejectedValue(apiError);

    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    const textarea = await screen.findByPlaceholderText(/saisissez votre texte/i);
    await user.type(textarea, 'Ce texte va échouer');
    
    await act(async () => {
      await user.click(screen.getByRole('button', { name: /traduire/i }));
    });

    expect(authService.logout).toHaveBeenCalledOnce();
    expect(mockedUsedNavigate).toHaveBeenCalledWith('/login', {
      state: { message: "Votre session a expiré. Veuillez vous reconnecter." },
    });
  });

  // CORRIGÉ : On utilise findAllBy...
  test('devrait mettre à jour automatiquement la langue cible si elle devient invalide', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);

    render(<BrowserRouter><TranslatorPage /></BrowserRouter>);

    // `findAllByRole` attend que les éléments apparaissent.
    const selects = await screen.findAllByRole('combobox');
    const sourceLangSelect = selects[0];
    const targetLangSelect = selects[1];

    expect(sourceLangSelect.value).toBe('fra_Latn');
    expect(targetLangSelect.value).toBe('ary_Arab');

    await user.selectOptions(sourceLangSelect, 'ary_Arab');
    await user.selectOptions(targetLangSelect, 'eng_Latn');
    expect(sourceLangSelect.value).toBe('ary_Arab');
    expect(targetLangSelect.value).toBe('eng_Latn');

    await user.selectOptions(sourceLangSelect, 'fra_Latn');

    expect(targetLangSelect.value).toBe('ary_Arab');
  });
});