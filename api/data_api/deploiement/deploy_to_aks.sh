#!/bin/bash

#================================================================
# SCRIPT 2: Déploiement sur le cluster AKS
#================================================================

set -e

# --- CONFIGURATION (À REMPLIR) ---
RESOURCE_GROUP="RG_FIGOUTI"
AKS_NAME="aks-darija-cluster"
K8S_CONFIG_FILE="./k8s/data-api.yaml"
K8S_SECRET_NAME="api-secrets"
# --- FIN DE LA CONFIGURATION ---


# --- DÉBUT DU SCRIPT ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Connexion à Azure et au cluster AKS
echo -e "${YELLOW}1. Connexion à Azure et configuration de kubectl...${NC}"
az login
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_NAME" --overwrite-existing
echo -e "${GREEN}Connecté au cluster AKS '$AKS_NAME'.${NC}\n"

# 2. Création du Secret Kubernetes à partir du fichier .env
echo -e "${YELLOW}2. Création/Mise à jour du secret Kubernetes '${K8S_SECRET_NAME}'...${NC}"
# On supprime l'ancien secret s'il existe, pour pouvoir le recréer avec les nouvelles valeurs
kubectl delete secret "$K8S_SECRET_NAME" --ignore-not-found=true

# On le crée à partir du fichier .env local
kubectl create secret generic "$K8S_SECRET_NAME" --from-env-file=.env
echo -e "${GREEN}Secret créé avec succès.${NC}\n"

# 3. Déploiement de l'application sur AKS
echo -e "${YELLOW}3. Déploiement de l'application via ${K8S_CONFIG_FILE}...${NC}"
kubectl apply -f "$K8S_CONFIG_FILE"
echo -e "${GREEN}Déploiement initié. Vérification du statut...${NC}\n"

# 4. Attente de l'adresse IP externe
echo -e "${YELLOW}Attente de l'adresse IP externe pour le service 'data-api-service'...${NC}"
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