#!/bin/bash

# 📍 Aller à la racine du projet
cd "$(dirname "$0")/.."

# 🔄 Charger les variables d’environnement
set -a
source .env
set +a

# ✅ Vérifier les variables nécessaires
if [[ -z "$SUPABASE_URL" || -z "$PG_LOCAL_PASSWORD" ]]; then
  echo "❌ Erreur : SUPABASE_URL ou PG_LOCAL_PASSWORD non défini dans .env"
  exit 1
fi

# 🔐 Utiliser le mot de passe local pour pg_dump
export PGPASSWORD="$PG_LOCAL_PASSWORD"

# 📤 Exporter la base locale
echo "📦 Export de la base locale 'darija_db'..."
pg_dump -U postgres -d darija_db -f darija_db.sql

if [[ $? -ne 0 ]]; then
  echo "❌ Échec de l'export avec pg_dump."
  exit 1
fi

# 📥 Importer dans Supabase
echo "🚀 Import vers Supabase..."
psql "$SUPABASE_URL" < darija_db.sql

if [[ $? -ne 0 ]]; then
  echo "❌ Échec de l'import avec psql."
  exit 1
fi

# 🧹 Supprimer le fichier temporaire après succès
rm darija_db.sql
echo "🧼 Fichier darija_db.sql supprimé."

echo "✅ Migration terminée avec succès vers Supabase !"
