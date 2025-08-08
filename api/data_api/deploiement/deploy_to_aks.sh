#!/bin/bash

#================================================================
# SCRIPT 2: Déploiement sur le cluster AKS
#=================================================================

set -e

# --- CONFIGURATION (À REMPLIR) ---
RESOURCE_GROUP="RG_FIGOUTI"
AKS_NAME="aks-darija-cluster"
ACR_NAME="iaapi"
IMAGE_NAME="darija-data-api"

# --- DÉTERMINATION AUTOMATIQUE DES CHEMINS (VERSION ROBUSTE) ---
# Trouve le répertoire où se trouve ce script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Remonte de 3 niveaux pour trouver la racine du projet (deploiement -> data_api -> api -> racine)
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

# Le chemin vers le fichier de configuration est maintenant absolu et fiable
K8S_CONFIG_FILE="${PROJECT_ROOT}/k8s/data-api.yaml"

# --- CONFIGURATION DES SECRETS (CHARGEMENT DEPUIS .env) ---
ENV_FILE_PATH="${PROJECT_ROOT}/.env"

if [ ! -f "$ENV_FILE_PATH" ]; then
    echo -e "\033[0;31mErreur: Fichier de configuration '${ENV_FILE_PATH}' introuvable.\033[0m"
    echo "Veuillez créer un fichier .env à la racine de votre projet avec toutes les variables nécessaires."
    exit 1
fi
source "$ENV_FILE_PATH"

# Vérification que les variables essentielles sont bien chargées
: ${ADMIN_USERNAME:?"La variable ADMIN_USERNAME doit être définie dans votre fichier .env"}
: ${ADMIN_PASSWORD:?"La variable ADMIN_PASSWORD doit être définie dans votre fichier .env"}
: ${SUPABASE_URL:?"La variable SUPABASE_URL doit être définie dans votre fichier .env"}
: ${JWT_SECRET:?"La variable JWT_SECRET doit être définie dans votre fichier .env"}
: ${BASE_URL:?"La variable BASE_URL doit être définie dans votre fichier .env"}
: ${VITE_DATA_API_BASE_URL:?"La variable VITE_DATA_API_BASE_URL doit être définie dans votre fichier .env"}
: ${VITE_IA_API_BASE_URL:?"La variable VITE_IA_API_BASE_URL doit être définie dans votre fichier .env"}
# --- FIN DE LA CONFIGURATION ---


# --- DÉBUT DU SCRIPT ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Étape 0 : Lire le tag de l'image à déployer
echo -e "${YELLOW}0. Lecture du tag de l'image à déployer...${NC}"
# Le chemin vers le fichier de tag est maintenant relatif au script
TAG_FILE="${SCRIPT_DIR}/last_build_tag.txt"
if [ ! -f "$TAG_FILE" ]; then
    echo -e "${RED}Erreur: Fichier de tag '${TAG_FILE}' introuvable.${NC}"
    echo "Veuillez d'abord exécuter le script 'build_and_push_data_api.sh'."
    exit 1
fi
IMAGE_TAG=$(cat "$TAG_FILE")
if [ -z "$IMAGE_TAG" ]; then
    echo -e "${RED}Erreur: Le fichier de tag est vide.${NC}"
    exit 1
fi
echo -e "${GREEN}Tag à déployer : ${IMAGE_TAG}${NC}\n"

# Étape 1 : Connexion à Azure et au cluster AKS
echo -e "${YELLOW}1. Connexion à Azure et configuration de kubectl...${NC}"
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_NAME" --overwrite-existing
echo -e "${GREEN}Connecté au cluster AKS '$AKS_NAME'.${NC}\n"

# Étape 2 : Suppression et recréation du secret 'api-secrets'
echo -e "${YELLOW}2. Mise à jour du secret 'api-secrets'...${NC}"
kubectl delete secret api-secrets --ignore-not-found=true
kubectl create secret generic api-secrets \
  --from-literal=ADMIN_USERNAME="$ADMIN_USERNAME" \
  --from-literal=ADMIN_PASSWORD="$ADMIN_PASSWORD" \
  --from-literal=SUPABASE_URL="$SUPABASE_URL" \
  --from-literal=JWT_SECRET="$JWT_SECRET" \
  --from-literal=BASE_URL="$BASE_URL" \
  --from-literal=VITE_DATA_API_BASE_URL="$VITE_DATA_API_BASE_URL" \
  --from-literal=VITE_IA_API_BASE_URL="$VITE_IA_API_BASE_URL"
echo -e "${GREEN}Le secret 'api-secrets' a été créé/mis à jour.${NC}\n"

# Étape 3 : Mise à jour dynamique du manifeste Kubernetes
echo -e "${YELLOW}3. Mise à jour du tag de l'image dans ${K8S_CONFIG_FILE}...${NC}"
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query "loginServer" --output tsv)
sed -i.bak "s|image: ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:.*|image: ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}|g" "$K8S_CONFIG_FILE"
echo -e "${GREEN}Manifeste mis à jour pour utiliser l'image '${IMAGE_NAME}:${IMAGE_TAG}'.${NC}\n"

# Étape 4 : Déploiement de l'application sur AKS
echo -e "${YELLOW}4. Déploiement de l'application via ${K8S_CONFIG_FILE}...${NC}"
kubectl apply -f "$K8S_CONFIG_FILE"
echo -e "${GREEN}Déploiement initié. Attente de la fin du redémarrage du pod...${NC}"
kubectl rollout status deployment/data-api-deployment --timeout=5m
echo -e "${GREEN}Le pod a été mis à jour avec succès.${NC}\n"

# Étape 5 : Attente de l'adresse IP externe
echo -e "${YELLOW}5. Attente de l'adresse IP externe pour le service 'data-api-service'...${NC}"
IP_ADDRESS=""
while [ -z "$IP_ADDRESS" ]; do
  echo "En attente de l'IP..."
  IP_ADDRESS=$(kubectl get service data-api-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  [ -z "$IP_ADDRESS" ] && sleep 10
done

echo "--------------------------------------------------"
echo -e "${GREEN}✅ Déploiement sur AKS terminé !${NC}"
echo -e "L'API est accessible à l'adresse : ${YELLOW}http://${IP_ADDRESS}:80${NC}"
echo "La documentation Swagger est disponible sur : http://${IP_ADDRESS}:80/docs"
echo "--------------------------------------------------"