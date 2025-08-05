// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    // AJOUTER/MODIFIER CETTE SECTION
    coverage: {
      provider: 'v8', // ou 'istanbul'
      reporter: ['text', 'json', 'html'], // Formats de rapport à générer
      // Exclure certains fichiers de l'analyse de couverture
      exclude: [
        'node_modules/',
        'src/setupTests.js',
        'src/main.jsx', // Souvent peu de logique testable ici
        '.*.js', // Exclure les fichiers de config comme vite.config.js
      ],
      // (Optionnel) Définir un seuil de couverture en pourcentage
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
})