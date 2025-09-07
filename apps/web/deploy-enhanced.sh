#!/bin/bash

echo "======================================"
echo "Enhanced Dashboard Deployment"
echo "======================================"
echo ""
echo "Pre-flight Checklist:"
echo "✓ Weather API endpoints added"
echo "✓ Market times API endpoints added"
echo "✓ Market data API endpoints added"
echo "✓ Enhanced header component created"
echo "✓ Portfolio chart component created"
echo "✓ Market data grid created"
echo ""

# Test API endpoints first
echo "Testing API endpoints..."
echo -n "Weather DC: "
curl -s https://mulroystreetcap.com/api/weather/dc | jq -r .temp_f > /dev/null 2>&1 && echo "✅" || echo "❌"

echo -n "Market Times: "
curl -s https://mulroystreetcap.com/api/market-times | jq . > /dev/null 2>&1 && echo "✅" || echo "❌"

echo -n "Market Data: "
curl -s https://mulroystreetcap.com/api/market-data | jq . > /dev/null 2>&1 && echo "✅" || echo "❌"

echo ""
read -p "Continue with deployment? (y/n): " proceed

if [ "$proceed" != "y" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Build
echo "Building dashboard..."
pnpm build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
cp -r out backups/out-pre-enhancement-$TIMESTAMP
echo "✅ Backup created: backups/out-pre-enhancement-$TIMESTAMP"

# Deploy
echo "Deploying to production..."
npx swa deploy ./out --deployment-token $(cat token.txt) --env production

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ DEPLOYMENT SUCCESSFUL!"
    echo ""
    echo "Dashboard: https://www.mulroystreetcap.com"
    echo "Rollback: ./restore-stable.sh"
    echo ""
    echo "Please check:"
    echo "1. Weather displays for DC and Asbury Park"
    echo "2. World market times show correctly"
    echo "3. Portfolio chart renders"
    echo "4. Market data updates"
else
    echo "❌ Deployment failed!"
    echo "Run ./restore-stable.sh to rollback"
fi