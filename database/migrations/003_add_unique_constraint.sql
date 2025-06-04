ALTER TABLE translations
ADD CONSTRAINT unique_translation_pair
UNIQUE (source_lang, source_text, target_lang, target_text);
