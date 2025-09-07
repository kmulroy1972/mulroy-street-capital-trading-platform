#!/bin/bash

set -e

# Configuration
RESOURCE_GROUP="rg-alpaca-trader-dev"
LOCATION="eastus2"
DEPLOYMENT_NAME="alpaca-trader-$(date +%Y%m%d-%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Alpaca Trader Infrastructure Deployment${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed${NC}"
    exit 1
fi

if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Not logged into Azure CLI${NC}"
    echo "Please run: az login"
    exit 1
fi

# Prompt for secure parameters
echo -e "${YELLOW}Please provide secure parameters:${NC}"
read -s -p "PostgreSQL admin password: " DB_ADMIN_PASSWORD
echo
read -s -p "Alpaca API Key ID: " ALPACA_API_KEY_ID
echo
read -s -p "Alpaca Secret Key: " ALPACA_SECRET_KEY
echo
read -s -p "JWT Secret (32+ chars): " JWT_SECRET
echo

# Validate inputs
if [[ -z "$DB_ADMIN_PASSWORD" || -z "$ALPACA_API_KEY_ID" || -z "$ALPACA_SECRET_KEY" || -z "$JWT_SECRET" ]]; then
    echo -e "${RED}❌ All secure parameters are required${NC}"
    exit 1
fi

if [[ ${#JWT_SECRET} -lt 32 ]]; then
    echo -e "${RED}❌ JWT Secret must be at least 32 characters${NC}"
    exit 1
fi

# Create resource group
echo -e "${YELLOW}Creating resource group: $RESOURCE_GROUP${NC}"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output table

# Validate Bicep template
echo -e "${YELLOW}Validating Bicep template...${NC}"
az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file main.bicep \
    --parameters @parameters.json \
    --parameters dbAdminPassword="$DB_ADMIN_PASSWORD" \
    --parameters alpacaApiKeyId="$ALPACA_API_KEY_ID" \
    --parameters alpacaSecretKey="$ALPACA_SECRET_KEY" \
    --parameters jwtSecret="$JWT_SECRET"

if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ Template validation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Template validation passed${NC}"

# Deploy infrastructure
echo -e "${YELLOW}Deploying infrastructure...${NC}"
DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file main.bicep \
    --parameters @parameters.json \
    --parameters dbAdminPassword="$DB_ADMIN_PASSWORD" \
    --parameters alpacaApiKeyId="$ALPACA_API_KEY_ID" \
    --parameters alpacaSecretKey="$ALPACA_SECRET_KEY" \
    --parameters jwtSecret="$JWT_SECRET" \
    --name "$DEPLOYMENT_NAME" \
    --output json)

if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"

# Extract outputs
echo -e "${YELLOW}Extracting deployment outputs...${NC}"
ACR_LOGIN_SERVER=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.containerRegistryLoginServer.value')
API_APP_URL=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.apiAppUrl.value')
KEY_VAULT_URI=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.keyVaultUri.value')
STATIC_WEB_APP_URL=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.staticWebAppUrl.value')
POSTGRES_FQDN=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.postgresServerFqdn.value')

# Display deployment summary
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "================================"
echo "Resource Group: $RESOURCE_GROUP"
echo "Container Registry: $ACR_LOGIN_SERVER"
echo "API URL: https://$API_APP_URL"
echo "Web App URL: https://$STATIC_WEB_APP_URL"
echo "Key Vault: $KEY_VAULT_URI"
echo "PostgreSQL Server: $POSTGRES_FQDN"
echo "================================"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Build and push Docker images to ACR"
echo "2. Update Container Apps with your application images"
echo "3. Configure Static Web App deployment"
echo "4. Run database migrations"

# Clear sensitive variables
unset DB_ADMIN_PASSWORD
unset ALPACA_API_KEY_ID
unset ALPACA_SECRET_KEY
unset JWT_SECRET