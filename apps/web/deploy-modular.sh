#!/bin/bash

echo "======================================"
echo "Modular Dashboard Deployment"
echo "======================================"
echo ""

# Show current component versions
echo "Current Component Versions:"
cat components/versions.json | jq '.components'
echo ""

# Update version timestamp
jq '.lastUpdate = now | todate' components/versions.json > /tmp/versions.json
mv /tmp/versions.json components/versions.json

# Build
echo "Building dashboard..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Create versioned backup
VERSION=$(date +%Y%m%d-%H%M%S)
mkdir -p backups/deploy-$VERSION
cp -r out backups/deploy-$VERSION/
cp components/versions.json backups/deploy-$VERSION/

echo "✅ Backup created: backups/deploy-$VERSION"

# Deploy
echo "Deploying to production..."
npx swa deploy ./out --deployment-token $(cat token.txt) --env production

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ DEPLOYMENT SUCCESSFUL"
    echo ""
    echo "Component versions deployed:"
    cat components/versions.json | jq '.components'
    echo ""
    echo "Dashboard: https://www.mulroystreetcap.com"
    echo "Rollback: cp -r backups/deploy-$VERSION/out ."
else
    echo "❌ Deployment failed!"
fi