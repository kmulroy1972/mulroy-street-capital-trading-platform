#!/bin/bash

# This script sets up GitHub secrets for CI/CD

REPO="YOUR_GITHUB_USERNAME/alpaca-trader"

echo "Setting up GitHub secrets for $REPO"
echo "Make sure you have GitHub CLI installed: brew install gh"
echo "And you're logged in: gh auth login"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI not found. Please install it first:"
    echo "  Mac: brew install gh"
    echo "  Linux: curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    exit 1
fi

# Check if logged in
if ! gh auth status &> /dev/null; then
    echo "Please login to GitHub CLI first: gh auth login"
    exit 1
fi

echo "Enter your GitHub repository (format: username/repo-name):"
read -r REPO

echo "Setting up secrets for $REPO..."

# Azure credentials (you'll need to create a service principal)
echo ""
echo "To get Azure credentials, run:"
echo "  az ad sp create-for-rbac --name alpaca-trader-deploy --role contributor --scopes /subscriptions/YOUR_SUBSCRIPTION_ID --sdk-auth"
echo ""
echo "Paste the JSON output here (press Enter twice when done):"
echo "{"

AZURE_CREDS=""
while IFS= read -r line; do
    if [ -z "$line" ]; then
        break
    fi
    AZURE_CREDS="$AZURE_CREDS$line"$'\n'
done

if [ -n "$AZURE_CREDS" ]; then
    echo "$AZURE_CREDS" | gh secret set AZURE_CREDENTIALS --repo $REPO
    echo "✅ AZURE_CREDENTIALS set"
fi

# Alpaca credentials
echo ""
echo "Enter your Alpaca API Key ID:"
read -r APCA_KEY_ID
if [ -n "$APCA_KEY_ID" ]; then
    echo "$APCA_KEY_ID" | gh secret set APCA_API_KEY_ID --repo $REPO
    echo "✅ APCA_API_KEY_ID set"
fi

echo "Enter your Alpaca Secret Key:"
read -s APCA_SECRET_KEY
if [ -n "$APCA_SECRET_KEY" ]; then
    echo "$APCA_SECRET_KEY" | gh secret set APCA_API_SECRET_KEY --repo $REPO
    echo "✅ APCA_API_SECRET_KEY set"
fi

# Azure Static Web Apps token
echo ""
echo "Enter your Azure Static Web Apps deployment token:"
read -r SWA_TOKEN
if [ -n "$SWA_TOKEN" ]; then
    echo "$SWA_TOKEN" | gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --repo $REPO
    echo "✅ AZURE_STATIC_WEB_APPS_API_TOKEN set"
fi

# JWT Secret
JWT_SECRET=$(openssl rand -hex 32)
echo "$JWT_SECRET" | gh secret set JWT_SECRET --repo $REPO
echo "✅ JWT_SECRET generated and set"

echo ""
echo "✅ All secrets configured!"
echo ""
echo "Next steps:"
echo "1. Push your code to GitHub"
echo "2. Go to your repository -> Settings -> Environments"
echo "3. Create 'production' and 'production-engine' environments"
echo "4. Add required reviewers for engine deployments"
echo "5. Deploy with: git push origin main"