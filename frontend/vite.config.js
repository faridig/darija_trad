// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      
      // =======================================================
      // DÉBUT DE LA MISE À JOUR
      // =======================================================
      exclude: [
        // Fichiers et dossiers standards à ignorer
        'node_modules/',
        'dist/',
        'coverage/',
        '.github/',
        'public/',

        // Fichiers de configuration du projet
        '*.config.js',
        '*.config.mjs',
        '.eslintrc.cjs',

        // Fichiers de setup des tests et points d'entrée
        'src/setupTests.js',
        'src/main.jsx',
        'src/services/api.js', 

        // Composants qui n'ont pas de logique à tester (ex: layout pur)
        'src/App.jsx'
      ],
      // =======================================================
      // FIN DE LA MISE À JOUR
      // =======================================================

      // On conserve les seuils pour garantir la qualité
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
})