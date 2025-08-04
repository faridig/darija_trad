#!/bin/bash

#================================================================
# SCRIPT 1: Build et Push de l'image de la data_api vers ACR
#================================================================

# Arrête le script si une commande échoue
set -e

# --- CONFIGURATION (À REMPLIR) ---
ACR_NAME="iaapi"                                  # Le nom de votre Azure Container Registry
IMAGE_NAME="darija-data-api"                      # Le nom de l'image à créer dans l'ACR
# --- FIN DE LA CONFIGURATION ---


# --- DÉBUT DU SCRIPT ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_TAG=$(git rev-parse --short HEAD)
if [ -z "$IMAGE_TAG" ]; then
  echo -e "${RED}Erreur: Impossible de récupérer le SHA du commit Git. Êtes-vous dans un dépôt Git ?${NC}"
  exit 1
fi
echo -e "${YELLOW}Le tag de l'image sera basé sur le commit Git : ${IMAGE_TAG}${NC}\n"


echo -e "${YELLOW}Vérification des prérequis...${NC}"
if ! command -v az &> /dev/null; then echo -e "${RED}Erreur: Azure CLI (az) n'est pas installé.${NC}"; exit 1; fi
if ! command -v docker &> /dev/null; then echo -e "${RED}Erreur: Docker n'est pas en cours d'exécution.${NC}"; exit 1; fi
echo -e "${GREEN}Prérequis validés.${NC}\n"

# 1. Connexion à Azure
echo -e "${YELLOW}1. Connexion à Azure...${NC}"


# 2. Connexion à Azure Container Registry (ACR)
echo -e "${YELLOW}2. Connexion à Azure Container Registry: ${ACR_NAME}...${NC}"
az acr login --name "$ACR_NAME"
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query "loginServer" --output tsv)
ACR_IMAGE_FULL_NAME="${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"
echo -e "${GREEN}Le nom complet de l'image sera : ${ACR_IMAGE_FULL_NAME}${NC}\n"

# 3. Construction de l'image Docker
DOCKERFILE_PATH="./api/data_api/Dockerfile"
BUILD_CONTEXT="."
echo -e "${YELLOW}3. Construction de l'image Docker...${NC}"
docker build --no-cache -f "$DOCKERFILE_PATH" -t "$ACR_IMAGE_FULL_NAME" "$BUILD_CONTEXT"
echo -e "${GREEN}Image construite avec succès.${NC}\n"

# 4. Push de l'image vers ACR
echo -e "${YELLOW}4. Push de l'image vers ACR...${NC}"
docker push "$ACR_IMAGE_FULL_NAME"

echo -n "${IMAGE_TAG}" > ./api/data_api/deploiement/last_build_tag.txt


echo "--------------------------------------------------"
echo -e "${GREEN}✅ Tâche terminée !${NC}"
echo -e "L'image ${YELLOW}${ACR_IMAGE_FULL_NAME}${NC} a été pushée avec succès sur ACR."
echo "Vous pouvez maintenant utiliser le second script pour la déployer."
echo "---------------------------------------------------"