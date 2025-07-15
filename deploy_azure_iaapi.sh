#!/bin/bash
# ==============================================================================
# SCRIPT DE DÉPLOIEMENT FINAL (V4) - Propre et complet
# ==============================================================================

# Arrête le script immédiatement si une commande échoue.
set -eu

# --- CHARGEMENT DES SECRETS DEPUIS LE FICHIER .env ---
echo "INFO: Chargement de la configuration depuis le fichier .env..."

if [ -f .env ]; then
    # Exporte les variables du .env dans l'environnement du script
    export $(grep -v '^#' .env | xargs)
else
    echo "ERREUR: Fichier .env non trouvé. Veuillez le créer avec les secrets nécessaires."
    exit 1
fi

# Vérification que TOUTES les variables essentielles sont bien chargées
if [ -z "${SUPABASE_URL}" ] || [ -z "${ADMIN_USERNAME}" ] || [ -z "${ADMIN_PASSWORD}" ] || [ -z "${OPENAI_API_KEY}" ] || [ -z "${HUGGINGFACE_TOKEN}" ]; then
    echo "ERREUR: Une ou plusieurs variables essentielles ne sont pas définies dans le fichier .env."
    echo "Vérifiez SUPABASE_URL, ADMIN_USERNAME, ADMIN_PASSWORD, OPENAI_API_KEY, HUGGINGFACE_TOKEN."
    exit 1
fi

echo "INFO: Secrets chargés avec succès depuis .env."

# --- CONFIGURATION DE BASE ---
echo "INFO: Chargement de la configuration..."
RESOURCE_GROUP="RG_FIGOUTI"
LOCATION="francecentral"
ACR_NAME="iaapi"
PLAN_NAME="plan-darija-api"
WEBAPP_NAME="darija-api-figouti-$(date +%s)"

# --- RÉCUPÉRATION DYNAMIQUE DU MOT DE PASSE ACR ---
echo "INFO: Récupération du mot de passe pour l'ACR '${ACR_NAME}'..."
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)
if [ -z "$ACR_PASSWORD" ]; then
    echo "ERREUR: Impossible de récupérer le mot de passe pour l'ACR. Vérifiez que vous êtes bien connecté à Azure (az login)."
    exit 1
fi
echo "INFO: Mot de passe ACR récupéré avec succès."


# --- DÉBUT DU DÉPLOIEMENT ---
echo "################################################################"
echo "### DÉBUT DU DÉPLOIEMENT DE L'APPLICATION '${WEBAPP_NAME}' ###"
echo "################################################################"

# --- ÉTAPE 1: Création du plan de service ---
echo "--- ÉTAPE 1: Vérification/Création du plan de service '${PLAN_NAME}' ---"
az appservice plan create --name $PLAN_NAME --resource-group $RESOURCE_GROUP --location $LOCATION --sku B1 --is-linux
echo "----------------------------------------------------------------"

# --- ÉTAPE 2: Création de la Web App SANS les identifiants ---
echo "--- ÉTAPE 2: Création de la Web App '${WEBAPP_NAME}' ---"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $PLAN_NAME \
  --name $WEBAPP_NAME \
  --multicontainer-config-type COMPOSE \
  --multicontainer-config-file "./api/ia_api/docker-compose.azure.yml"
echo "----------------------------------------------------------------"

# --- ÉTAPE 3: Configuration de TOUTES les variables en une seule fois ---
echo "--- ÉTAPE 3: Configuration des variables d'environnement ---"
sleep 15
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME \
  --settings \
    "DOCKER_REGISTRY_SERVER_URL=https://iaapi.azurecr.io" \
    "DOCKER_REGISTRY_SERVER_USERNAME=${ACR_NAME}" \
    "DOCKER_REGISTRY_SERVER_PASSWORD=${ACR_PASSWORD}" \
    "SUPABASE_URL=${SUPABASE_URL_VALUE}" \
    "ADMIN_USERNAME=${ADMIN_USERNAME_VALUE}" \
    "ADMIN_PASSWORD=${ADMIN_PASSWORD_VALUE}" \
    "OPENAI_API_KEY=${OPENAI_API_KEY_VALUE}" \
    "HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN_VALUE}" \
    "WEBSITES_CONTAINER_START_TIME_LIMIT=1800"

echo "----------------------------------------------------------------"

# --- ÉTAPE 4: Redémarrage final ---
echo "--- ÉTAPE 4: Redémarrage de l'application ---"
az webapp restart --resource-group $RESOURCE_GROUP --name $WEBAPP_NAME
echo "----------------------------------------------------------------"

echo ""
echo "################################################################"
echo "### ✅ DÉPLOIEMENT TERMINÉ !                                  ###"
echo "################################################################"
echo "Son URL est : https://${WEBAPP_NAME}.azurewebsites.net"
echo "Le démarrage initial peut prendre 5 à 10 minutes. Pour suivre les logs :"
echo "az webapp log tail --resource-group \"${RESOURCE_GROUP}\" --name \"${WEBAPP_NAME}\""