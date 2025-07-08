-- Migration 004 : idempotente – ajout des colonnes RGPD à users

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;
