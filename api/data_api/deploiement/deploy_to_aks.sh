#!/bin/bash

#================================================================
# SCRIPT 2: Déploiement sur le cluster AKS
# Ce script suppose que le secret 'api-secrets' existe déjà.
#================================================================

set -e

# --- CONFIGURATION (À REMPLIR) ---
RESOURCE_GROUP="RG_FIGOUTI"
AKS_NAME="aks-darija-cluster"
K8S_CONFIG_FILE="./k8s/data-api.yaml"
# --- FIN DE LA CONFIGURATION ---


# --- DÉBUT DU SCRIPT ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Connexion à Azure et au cluster AKS
echo -e "${YELLOW}1. Connexion à Azure et configuration de kubectl...${NC}"
# On commente 'az login' pour ne pas avoir à se reconnecter à chaque fois
# az login
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_NAME" --overwrite-existing
echo -e "${GREEN}Connecté au cluster AKS '$AKS_NAME'.${NC}\n"

# ===================================================================
# DÉBUT DE LA MODIFICATION : Suppression de la gestion du secret
#
# echo -e "${YELLOW}2. Création/Mise à jour du secret Kubernetes '${K8S_SECRET_NAME}'...${NC}"
# kubectl delete secret "$K8S_SECRET_NAME" --ignore-not-found=true
# kubectl create secret generic "$K8S_SECRET_NAME" --from-env-file=.env
# echo -e "${GREEN}Secret créé avec succès.${NC}\n"
#
# FIN DE LA MODIFICATION
# ===================================================================

# 2. Vérification de l'existence du secret 'api-secrets'
echo -e "${YELLOW}2. Vérification de l'existence du secret 'api-secrets'...${NC}"
if ! kubectl get secret api-secrets &> /dev/null; then
  echo -e "${RED}Erreur : Le secret 'api-secrets' est introuvable sur le cluster.${NC}"
  echo "Veuillez le créer via le workflow GitHub Actions ou manuellement avant de lancer ce script."
  exit 1
fi
echo -e "${GREEN}Le secret 'api-secrets' a été trouvé.${NC}\n"


# 3. Déploiement de l'application sur AKS
echo -e "${YELLOW}3. Déploiement de l'application via ${K8S_CONFIG_FILE}...${NC}"
kubectl apply -f "$K8S_CONFIG_FILE"
echo -e "${GREEN}Déploiement initié. Vérification du statut...${NC}\n"

# 4. Attente de l'adresse IP externe
echo -e "${YELLOW}4. Attente de l'adresse IP externe pour le service 'data-api-service'...${NC}"
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