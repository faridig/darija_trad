-- Modèle Physique de Données (MPD)

CREATE TABLE translations (
    id SERIAL PRIMARY KEY,
    source_lang VARCHAR(10),
    source_text TEXT,
    target_lang VARCHAR(10),
    target_text TEXT
);
