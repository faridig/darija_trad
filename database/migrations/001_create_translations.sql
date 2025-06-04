-- Migration 001 : structure initiale
CREATE TABLE IF NOT EXISTS translations (
    id SERIAL PRIMARY KEY,
    source_lang VARCHAR(10),
    source_text TEXT,
    target_lang VARCHAR(10),
    target_text TEXT
);
