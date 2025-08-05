#!/bin/bash

#================================================================
# SCRIPT 2: Déploiement sur le cluster AKS
#=================================================================

set -e

# --- CONFIGURATION (À REMPLIR) ---
RESOURCE_GROUP="RG_FIGOUTI"
AKS_NAME="aks-darija-cluster"
K8S_CONFIG_FILE="./k8s/data-api.yaml"
ACR_NAME="iaapi"
IMAGE_NAME="darija-data-api"

# --- CONFIGURATION DES SECRETS (À REMPLIR OU À CHARGER DEPUIS UN .env) ---
# ATTENTION: Ne mettez pas de secrets en clair ici si votre script est sur un dépôt public.
# Préférez charger un fichier .env ou utiliser les secrets de votre environnement.
# Exemple: source .env
ADMIN_USERNAME=${ADMIN_USERNAME:-"default_admin"}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-"default_password"}
SUPABASE_URL=${SUPABASE_URL:-"default_supabase_url"}
VITE_DATA_API_BASE_URL=${VITE_DATA_API_BASE_URL:-"default_data_api_url"}
VITE_IA_API_BASE_URL=${VITE_IA_API_BASE_URL:-"default_ia_api_url"}
# --- FIN DE LA CONFIGURATION ---


# --- DÉBUT DU SCRIPT ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Étape 0 : Lire le tag de l'image à déployer
# ... (cette partie ne change pas)
echo -e "${YELLOW}0. Lecture du tag de l'image à déployer...${NC}"
TAG_FILE="./api/data_api/deploiement/last_build_tag.txt"
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
# ... (cette partie ne change pas)
echo -e "${YELLOW}1. Connexion à Azure et configuration de kubectl...${NC}"
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_NAME" --overwrite-existing
echo -e "${GREEN}Connecté au cluster AKS '$AKS_NAME'.${NC}\n"

# ===================================================================
# DÉBUT DE LA MODIFICATION
# ===================================================================

# Étape 2 : Suppression et recréation du secret 'api-secrets'
echo -e "${YELLOW}2. Mise à jour du secret 'api-secrets'...${NC}"

# On supprime d'abord le secret s'il existe. '|| true' ignore l'erreur si le secret n'existe pas.
kubectl delete secret api-secrets --ignore-not-found=true

# On le recrée avec les valeurs actuelles.
# IMPORTANT: J'ai corrigé les clés dupliquées.
kubectl create secret generic api-secrets \
  --from-literal=ADMIN_USERNAME="$ADMIN_USERNAME" \
  --from-literal=ADMIN_PASSWORD="$ADMIN_PASSWORD" \
  --from-literal=SUPABASE_URL="$SUPABASE_URL" \
  --from-literal=BASE_URL="$BASE_URL" \
  --from-literal=DATA_API_BASE_URL="$VITE_DATA_API_BASE_URL" \
  --from-literal=IA_API_BASE_URL="$VITE_IA_API_BASE_URL"

echo -e "${GREEN}Le secret 'api-secrets' a été créé/mis à jour.${NC}\n"

# ===================================================================
# FIN DE LA MODIFICATION
# ===================================================================

# Étape 3 : Mise à jour dynamique du manifeste Kubernetes
# ... (cette partie ne change pas)
echo -e "${YELLOW}3. Mise à jour du tag de l'image dans ${K8S_CONFIG_FILE}...${NC}"
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query "loginServer" --output tsv)
sed -i.bak "s|image: ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:.*|image: ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}|g" "$K8S_CONFIG_FILE"
echo -e "${GREEN}Manifeste mis à jour pour utiliser l'image '${IMAGE_NAME}:${IMAGE_TAG}'.${NC}\n"

# Étape 4 : Déploiement de l'application sur AKS
# ... (cette partie ne change pas)
echo -e "${YELLOW}4. Déploiement de l'application via ${K8S_CONFIG_FILE}...${NC}"
kubectl apply -f "$K8S_CONFIG_FILE"
echo -e "${GREEN}Déploiement initié. Vérification du statut...${NC}\n"

# Étape 5 : Attente de l'adresse IP externe
# ... (cette partie ne change pas)
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