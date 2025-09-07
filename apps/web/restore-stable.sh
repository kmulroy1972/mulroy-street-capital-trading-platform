#!/bin/bash
echo "Restoring last stable version..."

# Find most recent stable backup
LATEST_STABLE=$(ls -dt backups/out-stable-* 2>/dev/null | head -1)

if [ -z "$LATEST_STABLE" ]; then
    echo "❌ No stable backup found!"
    exit 1
fi

echo "Restoring from: $LATEST_STABLE"
rm -rf out
cp -r $LATEST_STABLE out

echo "Redeploying stable version..."
npx swa deploy ./out --deployment-token $(cat token.txt) --env production

echo "✅ Stable version restored and deployed"
