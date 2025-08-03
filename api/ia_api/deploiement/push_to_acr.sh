#!/bin/bash

#================================================================================
# Script pour construire, tagger et pusher les images Docker du projet vers ACR.
# Conçu pour être exécuté depuis son propre dossier.
#================================================================================

# Arrête le script si une commande échoue
set -e

# --- Détermination des chemins ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"

# --- CONFIGURATION ---
ACR_NAME="iaapi"
IMAGE_VERSION="1.0.2"
COMPOSE_PROJECT_NAME="ia_api"

declare -A SERVICE_MAP
SERVICE_MAP=(
  ["app"]="darija-api"
  ["prometheus"]="darija-api-prometheus"
  ["grafana"]="darija-api-grafana"
)
# --- FIN DE LA CONFIGURATION ---


# --- DÉBUT DU SCRIPT ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Vérification des prérequis...${NC}"

if ! command -v az &> /dev/null; then
    echo "Erreur: Azure CLI (az) n'est pas installé."
    exit 1
fi
if ! docker info &> /dev/null; then
    echo "Erreur: Docker ne semble pas être en cours d'exécution."
    exit 1
fi
echo -e "${GREEN}Prérequis validés.${NC}\n"

# 1. Connexion à Azure Container Registry
echo -e "${YELLOW}1. Connexion à Azure Container Registry: ${ACR_NAME}...${NC}"
az acr login --name "$ACR_NAME"
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query "loginServer" --output tsv)
echo -e "${GREEN}Connexion à ${ACR_LOGIN_SERVER} réussie.${NC}\n"

# 2. Construction des images avec Docker Compose
echo -e "${YELLOW}2. Construction des images Docker via docker-compose...${NC}"
cd "${COMPOSE_DIR}"
echo "Contexte de build: $(pwd)"
# Utilisation de docker-compose (avec tiret)
docker-compose build --no-cache
echo -e "${GREEN}Images construites avec succès.${NC}\n"

# 3. Taggage et Push des images
echo -e "${YELLOW}3. Taggage et Push des images vers ACR...${NC}"

for service_name in "${!SERVICE_MAP[@]}"; do
    repo_name=${SERVICE_MAP[$service_name]}
    # Utilisation de l'underscore "_" pour le nom de l'image locale, comme le fait docker-compose
    local_image_tag="${COMPOSE_PROJECT_NAME}_${service_name}:latest"
    acr_image_tag="${ACR_LOGIN_SERVER}/${repo_name}:${IMAGE_VERSION}"
    
    echo "--------------------------------------------------"
    echo -e "Traitement du service: ${YELLOW}${service_name}${NC}"
    echo "  - Image locale: ${local_image_tag}"
    echo "  - Destination ACR: ${acr_image_tag}"
    
    echo "  - Taggage..."
    docker tag "$local_image_tag" "$acr_image_tag"
    
    echo "  - Push vers ACR..."
    docker push "$acr_image_tag"
    
    echo -e "  - ${GREEN}Push de l'image ${repo_name}:${IMAGE_VERSION} terminé.${NC}"
done

echo "--------------------------------------------------"
echo ""
cd "$SCRIPT_DIR"

echo -e "${GREEN}Toutes les images ont été pushées avec succès vers ${ACR_NAME} !${NC}"