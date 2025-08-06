#!/bin/sh

# Ce script est le point d'entrée de notre conteneur Docker.
# Son rôle est de transformer les variables d'environnement
# en un fichier de configuration lisible par notre application JavaScript.

# 1. On définit le chemin où sera créé notre fichier de configuration.
#    /usr/share/nginx/html/ est le dossier où Nginx (notre serveur web)
#    cherche les fichiers à servir.
CONFIG_FILE_PATH="/usr/share/nginx/html/config.js"

echo "Génération du fichier de configuration : ${CONFIG_FILE_PATH}"

# 2. On écrit le contenu du fichier JavaScript.
#    On crée un objet global `window.runtimeConfig` qui contiendra nos URLs.
echo "window.runtimeConfig = {" > ${CONFIG_FILE_PATH}
echo "  VITE_DATA_API_BASE_URL: '${VITE_DATA_API_BASE_URL}'," >> ${CONFIG_FILE_PATH}
echo "  VITE_IA_API_BASE_URL: '${VITE_IA_API_BASE_URL}'" >> ${CONFIG_FILE_PATH}
echo "};" >> ${CONFIG_FILE_PATH}

echo "--- Contenu du fichier config.js généré ---"
# On affiche le contenu du fichier pour pouvoir vérifier dans les logs
# que les bonnes valeurs ont bien été utilisées.
cat ${CONFIG_FILE_PATH}
echo "-------------------------------------------"

# 3. Une fois le fichier créé, on lance le serveur web Nginx.
#    L'option '-g daemon off;' est importante pour que le conteneur
#    reste en cours d'exécution.
echo "Démarrage de Nginx..."
exec nginx -g 'daemon off;'