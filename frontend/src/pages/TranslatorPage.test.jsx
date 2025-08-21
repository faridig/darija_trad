// frontend/src/pages/TranslatorPage.test.jsx (VERSION FINALE CORRIGÉE)

import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
// On importe MemoryRouter pour simuler la navigation en mémoire
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, test, expect, vi, beforeEach } from 'vitest';

import TranslatorPage from './TranslatorPage';
import { authService } from '../services/authService';
import { iaApi } from '../services/api';

// --- Mocks (inchangés) ---
vi.mock('../services/authService');
vi.mock('../services/api', () => ({
  iaApi: {
    post: vi.fn(),
  },
}));

// --- NOUVEAU : Wrapper de rendu ---
// Cette fonction nous permet de contrôler l'environnement de rendu.
const renderWithRouter = (ui, { initialEntries = ['/translate'] } = {}) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        {/* On définit une fausse page de login pour que la redirection fonctionne */}
        <Route path="/login" element={<div>Page de Login</div>} />
        {/* On définit la route pour notre composant à tester */}
        <Route path="/translate" element={ui} />
      </Routes>
    </MemoryRouter>
  );
};

// --- Début des tests ---
describe('TranslatorPage', () => {

  beforeEach(() => {
    vi.clearAllMocks();
    iaApi.post.mockClear();
  });

  // CORRIGÉ : On utilise notre wrapper pour le test de redirection.
  test('devrait rediriger vers /login si l\'utilisateur n\'est pas authentifié', async () => {
    authService.isAuthenticated.mockReturnValue(false);
    renderWithRouter(<TranslatorPage />, { initialEntries: ['/translate'] });
    // On vérifie que le texte de notre fausse page de login est bien affiché.
    expect(await screen.findByText('Page de Login')).toBeInTheDocument();
  });

  // CORRIGÉ : On utilise maintenant notre wrapper et getBy... redevient possible car le rendu est synchrone.
  test('devrait afficher la page du traducteur si l\'utilisateur est authentifié', () => {
    authService.isAuthenticated.mockReturnValue(true);
    renderWithRouter(<TranslatorPage />);
    expect(screen.getByRole('heading', { name: /traducteur darija/i })).toBeInTheDocument();
  });

  // On continue d'utiliser le wrapper pour tous les autres tests.
  test('devrait appeler l\'API de traduction et afficher le résultat', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    iaApi.post.mockResolvedValue({ data: { reponse: 'Salam alikoum' } });

    renderWithRouter(<TranslatorPage />);

    const textarea = screen.getByPlaceholderText(/saisissez votre texte/i);
    await user.type(textarea, 'Bonjour à tous');
    await user.click(screen.getByRole('button', { name: /traduire/i }));
    
    expect(await screen.findByText('Salam alikoum')).toBeInTheDocument();
  });
  
  // Le reste des tests suit la même logique : utiliser `renderWithRouter`
  // et les requêtes `getBy` ou `findBy` selon si l'action est synchrone ou asynchrone.

  test('devrait gérer une erreur de l\'API de traduction et afficher un message', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    iaApi.post.mockRejectedValue(new Error('API Error'));
    renderWithRouter(<TranslatorPage />);

    await user.type(screen.getByPlaceholderText(/saisissez votre texte/i), 'Test');
    await user.click(screen.getByRole('button', { name: /traduire/i }));
    
    expect(await screen.findByText(/Une erreur est survenue/i)).toBeInTheDocument();
  });

  test('devrait inverser les langues et les textes', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    iaApi.post.mockResolvedValue({ data: { reponse: 'Salam' } });
    renderWithRouter(<TranslatorPage />);

    const inputArea = screen.getByPlaceholderText(/saisissez votre texte/i);
    await user.type(inputArea, 'Bonjour');
    await user.click(screen.getByRole('button', { name: /traduire/i }));
    
    await screen.findByText('Salam'); // Attendre le résultat
    
    await user.click(screen.getByRole('button', { name: /inverser/i }));
    
    expect(inputArea.value).toBe('Salam');
    expect(screen.getByText('Bonjour')).toBeInTheDocument();
  });

  test('devrait appeler logout et rediriger au clic sur Déconnexion', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    renderWithRouter(<TranslatorPage />);

    await user.click(screen.getByRole('button', { name: /déconnexion/i }));
    
    expect(authService.logout).toHaveBeenCalledOnce();
    expect(await screen.findByText('Page de Login')).toBeInTheDocument();
  });

  test('devrait rediriger en cas d\'erreur 401', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    iaApi.post.mockRejectedValue({ response: { status: 401 } });
    renderWithRouter(<TranslatorPage />);

    await user.type(screen.getByPlaceholderText(/saisissez votre texte/i), 'test');
    await user.click(screen.getByRole('button', { name: /traduire/i }));
    
    expect(authService.logout).toHaveBeenCalledOnce();
    expect(await screen.findByText('Page de Login')).toBeInTheDocument();
  });

  test('devrait mettre à jour la langue cible automatiquement', async () => {
    const user = userEvent.setup();
    authService.isAuthenticated.mockReturnValue(true);
    renderWithRouter(<TranslatorPage />);

    const selects = screen.getAllByRole('combobox');
    const sourceLangSelect = selects[0];
    const targetLangSelect = selects[1];
    
    await user.selectOptions(sourceLangSelect, 'ary_Arab');
    await user.selectOptions(targetLangSelect, 'eng_Latn');

    await user.selectOptions(sourceLangSelect, 'fra_Latn');

    expect(targetLangSelect.value).toBe('ary_Arab');
  });
});