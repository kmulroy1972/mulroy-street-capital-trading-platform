#!/bin/bash
set -e

echo "=== MANUAL TEST CHANGE ==="
echo "Adding 'ADMIN PANEL WORKS!' text to dashboard"
echo "Started: $(date)"

cd /home/ktmulroy/apps/web

# Backup the current file
cp components/modules/Header.tsx components/modules/Header.tsx.backup-manual-$(date +%Y%m%d-%H%M%S)

# Add test text to the LIVE status
/usr/bin/sed -i 's/<span className="text-sm">LIVE<\/span>/<span className="text-sm">LIVE - ADMIN PANEL WORKS!<\/span>/g' components/modules/Header.tsx

echo "Modified header file"

# Build the project
echo "Building..."
export PATH=/usr/bin:/bin:$PATH
npm run build

if [ $? -eq 0 ]; then
    echo "Build successful, deploying..."
    npx swa deploy ./out --deployment-token $(cat token.txt) --env production
    
    if [ $? -eq 0 ]; then
        echo "✅ SUCCESS! Check https://www.mulroystreetcap.com"
        echo "Should now show 'LIVE - ADMIN PANEL WORKS!' in header"
        echo "Completed: $(date)"
    else
        echo "❌ Deployment failed"
        exit 1
    fi
else
    echo "❌ Build failed"
    exit 1
fi
