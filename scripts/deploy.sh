#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
RESOURCE_GROUP="rg-alpaca-trader-prod"
LOCATION="eastus2"
ENVIRONMENT="production"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Alpaca Trading System Deployment${NC}"
echo -e "${GREEN}================================${NC}"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

# Login to Azure
echo -e "\n${YELLOW}Logging in to Azure...${NC}"
az login

# Create resource group
echo -e "\n${YELLOW}Creating resource group...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy infrastructure
echo -e "\n${YELLOW}Deploying infrastructure...${NC}"
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/main.bicep \
  --parameters environmentName=alpaca-prod \
  --parameters dbAdminPassword="$(openssl rand -base64 32)" \
  --parameters alpacaApiKeyId="$APCA_API_KEY_ID" \
  --parameters alpacaSecretKey="$APCA_API_SECRET_KEY" \
  --parameters jwtSecret="$(openssl rand -hex 32)" \
  --output table

# Get outputs
ACR_LOGIN_SERVER=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs.containerRegistryLoginServer.value -o tsv)

API_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs.apiAppUrl.value -o tsv)

WEB_URL=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main \
  --query properties.outputs.staticWebAppUrl.value -o tsv)

# Build and push images
echo -e "\n${YELLOW}Building and pushing Docker images...${NC}"

# Login to ACR
az acr login --name ${ACR_LOGIN_SERVER%%.*}

# Build API
echo -e "\n${YELLOW}Building API image...${NC}"
docker build -t $ACR_LOGIN_SERVER/alpaca-api:latest -f apps/api/Dockerfile .
docker push $ACR_LOGIN_SERVER/alpaca-api:latest

# Build Engine
echo -e "\n${YELLOW}Building Engine image...${NC}"
docker build -t $ACR_LOGIN_SERVER/alpaca-engine:latest -f apps/engine/Dockerfile .
docker push $ACR_LOGIN_SERVER/alpaca-engine:latest

# Deploy containers
echo -e "\n${YELLOW}Deploying containers...${NC}"

# Update API
az containerapp update \
  --name alpaca-trader-production-api \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_LOGIN_SERVER/alpaca-api:latest

# Update Engine (with confirmation)
echo -e "\n${YELLOW}Deploy trading engine? This will start LIVE trading! (y/n)${NC}"
read -r response
if [[ "$response" == "y" ]]; then
    echo -e "${RED}WARNING: Deploying LIVE trading engine!${NC}"
    az containerapp update \
      --name alpaca-trader-production-engine \
      --resource-group $RESOURCE_GROUP \
      --image $ACR_LOGIN_SERVER/alpaca-engine:latest
    
    echo -e "${GREEN}Engine deployed - monitoring for health...${NC}"
    sleep 60
    
    # Check health
    az containerapp show \
      --name alpaca-trader-production-engine \
      --resource-group $RESOURCE_GROUP \
      --query "properties.runningStatus"
fi

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "API URL: https://${API_URL}"
echo -e "Web URL: https://${WEB_URL}"
echo -e "\n${YELLOW}Remember to:${NC}"
echo -e "1. Update DNS records"
echo -e "2. Configure SSL certificates"
echo -e "3. Set up monitoring alerts"
echo -e "4. Verify health checks"