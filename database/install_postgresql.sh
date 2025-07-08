#!/bin/bash
set -e  # Arrête le script en cas d'erreur

# Fonction d'aide au debug : affiche les logs et quitte
_show_logs_and_exit() {
  local svc=$1
  echo
  echo "❌ Échec du démarrage du service $svc. Voici les 30 dernières lignes de logs :"
  sudo journalctl -xeu "$svc" --no-pager | tail -n30
  exit 1
}

echo "📄 Chargement des variables d'environnement depuis .env..."
cd "$(dirname "$0")/.." || { echo "❌ Impossible de se placer dans le dossier du projet."; exit 1; }
[ -f .env ] || { echo "❌ .env introuvable."; exit 1; }
export $(grep -v '^#' .env | xargs)

echo "🔍 DB_NAME=$DB_NAME | DB_USER=$DB_USER"
[ -n "$DB_NAME" ] && [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ] \
  || { echo "❌ DB_NAME, DB_USER ou DB_PASSWORD manquant."; exit 1; }

echo "🔧 Mise à jour des paquets et installation de PostgreSQL..."
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Détection de la version installée
PG_VERSION=$(ls /etc/postgresql)
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

echo "🛑 Arrêt de PostgreSQL pour configuration..."
if command -v pg_ctlcluster >/dev/null; then
  sudo pg_ctlcluster "$PG_VERSION" main stop || true
else
  sudo service postgresql stop || true
fi

echo "🔍 Examen du fichier pg_hba.conf existant..."
if [ -f "$PG_HBA" ]; then
  echo "📝 Contenu problématique autour de la ligne 133:"
  sudo sed -n '130,140p' "$PG_HBA" || echo "Impossible d'afficher le contenu"
fi

echo "🛠 Backup et recréation de $PG_HBA..."
# Sauvegarde du fichier original
sudo cp "$PG_HBA" "${PG_HBA}.bak.$(date +%Y%m%d_%H%M%S)"

# Création d'un nouveau fichier pg_hba.conf propre
sudo tee "$PG_HBA" > /dev/null << 'EOF'
# PostgreSQL Client Authentication Configuration File
# ===================================================
#
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             postgres                                md5
local   all             all                                     md5

# IPv4 local connections:
host    all             all             127.0.0.1/32            md5

# IPv6 local connections:
host    all             all             ::1/128                 md5

# Allow replication connections from localhost, by a user with the
# replication privilege.
local   replication     all                                     peer
host    replication     all             127.0.0.1/32            md5
host    replication     all             ::1/128                 md5
EOF

# Vérification des permissions
sudo chown postgres:postgres "$PG_HBA"
sudo chmod 640 "$PG_HBA"

echo "✅ Nouveau fichier pg_hba.conf créé"

echo "🚀 Démarrage du cluster PostgreSQL ${PG_VERSION}/main..."
if command -v pg_ctlcluster >/dev/null; then
  if ! sudo pg_ctlcluster "$PG_VERSION" main start; then
    _show_logs_and_exit "postgresql@${PG_VERSION}-main.service"
  fi
else
  if ! sudo service postgresql start; then
    _show_logs_and_exit "postgresql.service"
  fi
fi

echo "🧪 Vérification du service…"
sleep 2  # Petit délai pour que le service démarre
if pg_isready | grep -q "accepting connections"; then
  echo "✅ PostgreSQL est opérationnel."
else
  _show_logs_and_exit "postgresql@${PG_VERSION}-main.service"
fi

# 🛠 Création de la base & de l'utilisateur si nécessaire
echo "🛠 Création de la base & de l'utilisateur si nécessaire…"
if sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" | grep -q 1; then
  echo "ℹ️ La base '$DB_NAME' existe déjà."
else
  echo "📚 Création de la base '$DB_NAME'…"
  sudo -u postgres createdb "$DB_NAME"
fi

if sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER';" | grep -q 1; then
  echo "ℹ️ L'utilisateur '$DB_USER' existe déjà."
else
  echo "👤 Création de l'utilisateur '$DB_USER'…"
  sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
fi

echo "🔐 Attribution des privilèges…"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Vérification de la connexion
echo "🧪 Vérification de la connexion..."
if ! PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "SELECT 1;" >/dev/null 2>&1; then
  echo "❌ Impossible de se connecter à la base de données"
  echo "🔍 Test de connexion détaillé:"
  PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "SELECT 1;" || true
  exit 1
fi

echo "✅ Installation terminée avec authentification md5."


# 🚀 Option migrations
read -p "Exécuter run_migrations.py maintenant ? (y/n) " run_script
if [[ "$run_script" == "y" ]]; then
  echo "🚀 Lancement des migrations en LOCAL…"

  ORIGINAL_SUPABASE_URL="$SUPABASE_URL"

  echo "ℹ️ Temporisation de SUPABASE_URL (vide) pour Python…"
  SUPABASE_URL="" python3 -m database.migrations.run_migrations

  # On remet la vraie valeur pour la suite
  export SUPABASE_URL="$ORIGINAL_SUPABASE_URL"
  echo "ℹ️ SUPABASE_URL restauré pour la migration vers Supabase."

else
  echo "ℹ️ Lance plus tard : python3 database/migrations/run_migrations.py"
fi




# 🚀 Option migration vers Supabase
read -p "Souhaites-tu maintenant lancer la migration vers Supabase (migrate_to_supabase.sh) ? (y/n) " run_supabase
if [[ "$run_supabase" == "y" ]]; then
  echo "🚀 Lancement du script de migration vers Supabase…"
  bash database/migrate_to_supabase.sh || { echo "❌ Échec lors de la migration vers Supabase."; exit 1; }
else
  echo "ℹ️ Tu pourras plus tard lancer : bash database/migrate_to_supabase.sh"
fi

