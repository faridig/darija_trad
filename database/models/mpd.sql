-- Modèle Physique de Données (MPD) 

CREATE TABLE translations (
    id SERIAL PRIMARY KEY,
    source_lang VARCHAR(10),
    source_text TEXT,
    target_lang VARCHAR(10),
    target_text TEXT
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login TIMESTAMPTZ
);
