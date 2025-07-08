-- Migration 003 : ajout idempotent de la contrainte unique sur translations

-- On supprime la contrainte si elle existe déjà
ALTER TABLE translations
  DROP CONSTRAINT IF EXISTS unique_translation_pair;

-- Puis on l’ajoute
ALTER TABLE translations
  ADD CONSTRAINT unique_translation_pair
  UNIQUE (source_lang, source_text, target_lang, target_text);
