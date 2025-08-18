#!/bin/bash

# --- Etape 1 : Se Placer au Bon Endroit ---

# `dirname "$0"` recupere le nom du dossier ou se trouve ce script.
# `"/.."` signifie "remonter d'un dossier".
# `cd` se deplace donc a la racine de votre projet.
# C'est crucial pour que la commande `source .env` fonctionne correctement.
cd "$(dirname "$0")/.."

# --- Etape 2 : Charger la Configuration ---

# `set -a` est une commande qui dit au shell : "A partir de maintenant,
# toutes les variables que tu creeras seront automatiquement marquees
# comme 'exportees'". Cela signifie qu'elles seront disponibles pour
# toutes les autres commandes que ce script lancera (comme psql, pg_dump).
set -a

# `source .env` lit le fichier .env ligne par ligne et cree des variables
# d'environnement pour chaque ligne (par exemple, SUPABASE_URL=...).
# Grace a `set -a`, ces variables sont immediatement exportees.
source .env

# `set +a` arrete le mode "exportation automatique". C'est une bonne pratique
# de ne l'activer que lorsque c'est necessaire.
set +a

# --- Etape 3 : Verifier que la Configuration est Complete ---

# On verifie si les variables SUPABASE_URL et PG_LOCAL_PASSWORD sont vides.
# `[[ -z "$VARIABLE" ]]` est une condition qui est vraie si la variable est vide.
if [[ -z "$SUPABASE_URL" || -z "$PG_LOCAL_PASSWORD" ]]; then
  # Si l'une des deux est vide, on affiche un message d'erreur clair...
  echo "Erreur : SUPABASE_URL ou PG_LOCAL_PASSWORD non defini dans .env"
  # ...et on arrete le script immediatement avec un code d'erreur.
  exit 1
fi

# --- Etape 4 : S'Authentifier aupres de la Base de Donnees Locale ---

# La commande `pg_dump` va demander un mot de passe pour se connecter
# a la base de donnees locale. Pour eviter que le script ne se bloque en
# attendant une saisie manuelle, on utilise la variable d'environnement
# `PGPASSWORD`. `pg_dump` la detecte automatiquement et l'utilise pour
# s'authentifier.
export PGPASSWORD="$PG_LOCAL_PASSWORD"

# --- Etape 5 : Exporter la Base de Donnees Locale ---

echo "Export de la base locale 'darija_db'..."
# On lance la commande d'exportation :
# -U postgres        : Se connecter avec l'utilisateur 'postgres' (l'admin local).
# -d darija_db       : Cibler la base de donnees nommee 'darija_db'.
# -f darija_db.sql   : Ecrire le resultat dans un fichier nomme 'darija_db.sql'.
pg_dump -U postgres -d darija_db -f darija_db.sql

# `$?` est une variable speciale qui contient le code de sortie de la
# derniere commande executee. `0` signifie succes, tout autre chiffre
# signifie echec.
# `if [[ $? -ne 0 ]]` signifie "si la derniere commande a echoue...".
if [[ $? -ne 0 ]]; then
  echo "Echec de l'export avec pg_dump."
  # On arrete le script pour ne pas essayer d'importer un fichier vide ou corrompu.
  exit 1
fi

# --- Etape 6 : Importer les Donnees dans Supabase ---

echo "Import vers Supabase..."
# On lance le client PostgreSQL :
# `psql "$SUPABASE_URL"` : Se connecte a la base de donnees distante en utilisant
#                        l'URL complete fournie par Supabase.
# `< darija_db.sql`      : C'est une "redirection d'entree". Cela dit a `psql`
#                        de lire et d'executer toutes les commandes SQL qui se
#                        trouvent dans le fichier `darija_db.sql`.
psql "$SUPABASE_URL" < darija_db.sql

# On verifie a nouveau si l'importation a reussi.
if [[ $? -ne 0 ]]; then
  echo "Echec de l'import avec psql."
  exit 1
fi

# --- Etape 7 : Nettoyer ---

# Si tout s'est bien passe, on n'a plus besoin du fichier d'export
# qui peut contenir des donnees sensibles.
rm darija_db.sql
echo "Fichier darija_db.sql supprime."

# --- Etape 8 : Confirmer le Succes ---

echo "Migration terminee avec succes vers Supabase !"