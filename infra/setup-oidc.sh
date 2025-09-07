#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Setting up GitHub OIDC Federation for Azure${NC}"

# Configuration
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
APP_NAME="alpaca-trader-github-actions"

# Prompt for GitHub repository information
echo -e "${YELLOW}GitHub Repository Configuration:${NC}"
read -p "GitHub organization/username: " GITHUB_ORG
read -p "Repository name: " GITHUB_REPO
read -p "Branch name (default: main): " GITHUB_BRANCH
GITHUB_BRANCH=${GITHUB_BRANCH:-main}

if [[ -z "$GITHUB_ORG" || -z "$GITHUB_REPO" ]]; then
    echo -e "${RED}❌ GitHub organization and repository name are required${NC}"
    exit 1
fi

GITHUB_REPO_FULL="$GITHUB_ORG/$GITHUB_REPO"

echo -e "${YELLOW}Creating Azure AD Application...${NC}"

# Create Azure AD application
APP_ID=$(az ad app create \
    --display-name "$APP_NAME" \
    --query appId -o tsv)

echo -e "${GREEN}✅ Created Azure AD Application: $APP_ID${NC}"

# Create service principal
echo -e "${YELLOW}Creating Service Principal...${NC}"
OBJECT_ID=$(az ad sp create --id "$APP_ID" --query id -o tsv)

echo -e "${GREEN}✅ Created Service Principal: $OBJECT_ID${NC}"

# Create federated credential for main branch
echo -e "${YELLOW}Creating federated credential for main branch...${NC}"
az ad app federated-credential create \
    --id "$APP_ID" \
    --parameters "{
        \"name\": \"$GITHUB_REPO-main\",
        \"issuer\": \"https://token.actions.githubusercontent.com\",
        \"subject\": \"repo:$GITHUB_REPO_FULL:ref:refs/heads/$GITHUB_BRANCH\",
        \"audiences\": [\"api://AzureADTokenExchange\"]
    }"

# Create federated credential for pull requests
echo -e "${YELLOW}Creating federated credential for pull requests...${NC}"
az ad app federated-credential create \
    --id "$APP_ID" \
    --parameters "{
        \"name\": \"$GITHUB_REPO-pr\",
        \"issuer\": \"https://token.actions.githubusercontent.com\",
        \"subject\": \"repo:$GITHUB_REPO_FULL:pull_request\",
        \"audiences\": [\"api://AzureADTokenExchange\"]
    }"

# Assign Contributor role to the service principal
echo -e "${YELLOW}Assigning Contributor role...${NC}"
az role assignment create \
    --assignee "$OBJECT_ID" \
    --role "Contributor" \
    --scope "/subscriptions/$SUBSCRIPTION_ID"

echo -e "${GREEN}✅ OIDC Federation setup complete!${NC}"
echo
echo -e "${YELLOW}GitHub Secrets to configure:${NC}"
echo "Add these secrets to your GitHub repository settings:"
echo "  AZURE_CLIENT_ID: $APP_ID"
echo "  AZURE_TENANT_ID: $(az account show --query tenantId -o tsv)"
echo "  AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo
echo -e "${YELLOW}GitHub Repository: https://github.com/$GITHUB_REPO_FULL/settings/secrets/actions${NC}"
echo
echo -e "${GREEN}🚀 Your GitHub Actions can now authenticate to Azure without passwords!${NC}"