// frontend/src/setupTests.js
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Étend l'objet 'expect' de Vitest avec les matchers de jest-dom
expect.extend(matchers);

// Exécute un nettoyage (démontage des composants) après chaque test
// pour éviter les fuites de mémoire et les interférences entre tests.
afterEach(() => {
  cleanup();
});