#!/bin/bash

set -e

# Configuration
RESOURCE_GROUP="rg-alpaca-trader-dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}⚠️  Alpaca Trader Infrastructure Cleanup${NC}"
echo "This will DELETE the entire resource group: $RESOURCE_GROUP"
echo "All resources including databases, container apps, and data will be permanently removed."
echo

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Not logged into Azure CLI${NC}"
    echo "Please run: az login"
    exit 1
fi

# Check if resource group exists
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    echo -e "${YELLOW}ℹ️  Resource group $RESOURCE_GROUP does not exist${NC}"
    exit 0
fi

# Confirmation prompt
read -p "Are you sure you want to delete the resource group '$RESOURCE_GROUP'? (yes/no): " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
    echo -e "${YELLOW}❌ Cleanup cancelled${NC}"
    exit 0
fi

# Final confirmation for production
ENVIRONMENT=$(az group show --name "$RESOURCE_GROUP" --query "tags.environment" -o tsv 2>/dev/null || echo "unknown")
if [[ "$ENVIRONMENT" == "prod" || "$ENVIRONMENT" == "production" ]]; then
    echo -e "${RED}🚨 WARNING: This appears to be a PRODUCTION environment!${NC}"
    read -p "Type 'DELETE PRODUCTION' to confirm: " PROD_CONFIRM
    if [[ "$PROD_CONFIRM" != "DELETE PRODUCTION" ]]; then
        echo -e "${YELLOW}❌ Production cleanup cancelled${NC}"
        exit 0
    fi
fi

echo -e "${YELLOW}🗑️  Starting cleanup...${NC}"

# List resources before deletion
echo -e "${YELLOW}Resources to be deleted:${NC}"
az resource list --resource-group "$RESOURCE_GROUP" --output table

echo
read -p "Proceed with deletion? (yes/no): " FINAL_CONFIRM
if [[ "$FINAL_CONFIRM" != "yes" ]]; then
    echo -e "${YELLOW}❌ Cleanup cancelled${NC}"
    exit 0
fi

# Delete the resource group and all its resources
echo -e "${YELLOW}Deleting resource group: $RESOURCE_GROUP${NC}"
az group delete \
    --name "$RESOURCE_GROUP" \
    --yes \
    --no-wait

echo -e "${GREEN}✅ Cleanup initiated successfully!${NC}"
echo "Note: Resource deletion is running in the background and may take several minutes to complete."
echo "You can monitor progress in the Azure portal or with:"
echo "  az group show --name $RESOURCE_GROUP"