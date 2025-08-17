#!/bin/bash


PROJECT_DIR="/projets/darija_app_final"


# Se déplacer à la racine du projet
cd "$PROJECT_DIR" || exit

# Activer l'environnement virtuel Python
# Assurez-vous que le chemin vers votre venv est correct
source "$PROJECT_DIR/venv/bin/activate"

echo "Environnement virtuel activé. Lancement du script de nettoyage..."

# Lancer le script Python de nettoyage
# Le script redirige sa sortie (logs) vers un fichier pour le débogage.
python3 -m database.maintenance.cleanup_inactive_users >> "$PROJECT_DIR/database/maintenance/cleanup.log" 2>&1

echo "Script terminé."

# Désactiver l'environnement virtuel (bonne pratique)
deactivate
