// frontend/src/services/authService.test.jsx

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { authService } from '../authService';
import { dataApi } from '../api';

// On mocke 'axios' (via notre instance dataApi)
vi.mock('../api', () => ({
  dataApi: {
    post: vi.fn(),
  },
}));

describe('authService', () => {

  beforeEach(() => {
    // Nettoyer les mocks et localStorage avant chaque test
    vi.clearAllMocks();
    localStorage.clear();
  });

  test('login devrait appeler l\'API et stocker le token dans localStorage', async () => {
    const mockToken = 'fake-jwt-token';
    dataApi.post.mockResolvedValue({ data: { access_token: mockToken } });

    await authService.login('user', 'pass');

    // Vérifie que l'API a été appelée correctement
    expect(dataApi.post).toHaveBeenCalledWith('/login', expect.any(URLSearchParams), expect.any(Object));
    // Vérifie que le token est bien stocké
    expect(localStorage.getItem('jwt_token')).toBe(mockToken);
  });

  test('register devrait appeler l\'API avec les bonnes données', async () => {
    const userData = { username: 'newuser', password: 'newpassword' };
    dataApi.post.mockResolvedValue({ data: { id: 1, ...userData } });

    await authService.register(userData.username, userData.password);

    expect(dataApi.post).toHaveBeenCalledWith('/register', userData);
  });

  test('logout devrait supprimer le token de localStorage', () => {
    localStorage.setItem('jwt_token', 'some-token');
    authService.logout();
    expect(localStorage.getItem('jwt_token')).toBeNull();
  });

  test('isAuthenticated devrait retourner true si un token existe', () => {
    localStorage.setItem('jwt_token', 'some-token');
    expect(authService.isAuthenticated()).toBe(true);
  });

  test('isAuthenticated devrait retourner false si aucun token n\'existe', () => {
    expect(authService.isAuthenticated()).toBe(false);
  });
});